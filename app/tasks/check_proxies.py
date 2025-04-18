import asyncio
import datetime
from ipaddress import IPv4Address, IPv6Address, ip_address
from typing import NamedTuple

import aiohttp
import aiohttp.client_exceptions
from aiohttp_socks import ProxyConnectionError, ProxyConnector, ProxyError

from app.core.database import create_session_factory
from app.core.uow import SQLUnitOfWork
from app.models.proxy import Protocol, Proxy
from app.service.proxy import ProxyService

HTTP_STATUS_OK = 200


class ProxyHttpResult(NamedTuple):
    """
    Represents the result of an HTTP call through a proxy.

    Attributes:
        time (int): The response time in milliseconds.
        status (int): The HTTP status code returned by the request.
        text (str): The body of the response (only for successful 2xx responses).
    """

    time: int
    status: int
    text: str


def format_proxy_url(
    address: IPv4Address | IPv6Address,
    port: int,
    protocol: Protocol,
    login: str | None = None,
    password: str | None = None,
) -> str:
    """
    Format a proxy URL based on the given parameters.

    Args:
        address (IPv4Address | IPv6Address): The IP address of the proxy.
        port (int): The port number of the proxy.
        protocol (Protocol): The protocol used by the proxy.
        login (str, optional): The username for proxy authentication. Defaults to None.
        password (str, optional): The password for proxy authentication. Defaults to None.

    Returns:
        str: A formatted proxy URL string.
    """
    credentials = ""
    if protocol == Protocol.SOCKS5 and login and password:
        credentials = f"{login}:{password}@"

    protocol_value = protocol.value
    if protocol == Protocol.HTTPS:  # aiohttp support only http with tls
        protocol_value = "http"

    return f"{protocol_value}://{credentials}{address}:{port}".lower()


async def graceful_shutdown(protocol: Protocol) -> None:
    """
    Ensure graceful shutdown of the aiohttp connection.

    For HTTPS, waits briefly to allow SSL connections to close properly.
    Refer to aiohttp docs:
    https://docs.aiohttp.org/en/stable/client_advanced.html#graceful-shutdown

    Args:
        protocol (Protocol): The protocol used by the proxy.
    """
    if protocol == Protocol.HTTPS:
        # Wait 250 ms for the underlying SSL connections to close
        await asyncio.sleep(0.250)
    else:
        # Zero-sleep to allow underlying connections to close
        await asyncio.sleep(0)


async def try_http_call_with_proxy(
    url: str,
    proxy_url: str,
    protocol: Protocol,
    proxy_timeout: int = 10,
) -> ProxyHttpResult | None:
    """
    Attempt to make an HTTP GET request through a given proxy.

    This function supports both HTTP/HTTPS and SOCKS4/SOCKS5 proxies. It measures the
    response time and optionally returns the response body for successful requests.

    Args:
        url (str): The target URL to perform a GET request on.
        proxy_url (str): The proxy server URL.
        protocol (Protocol): The protocol of the proxy (e.g., HTTP, SOCKS5).
        proxy_timeout (int, optional): Timeout in seconds for proxy connection and response. Defaults to 10.

    Returns:
        ProxyHttpResult | None: A ProxyHttpResult object if the request was successful, None otherwise.
    """
    proxy = None
    connector = None

    if protocol in (Protocol.SOCKS4, Protocol.SOCKS5):
        connector = ProxyConnector.from_url(proxy_url)
    else:  # HTTP, HTTPS
        proxy = proxy_url

    timeout = aiohttp.ClientTimeout(
        total=None,
        connect=proxy_timeout,
        sock_connect=proxy_timeout,
        sock_read=proxy_timeout,
    )

    try:
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            loop = asyncio.get_running_loop()
            start_time = loop.time()
            async with session.get(url=url, proxy=proxy) as resp:
                duration = int((loop.time() - start_time) * 1_000)  # seconds to milliseconds
                body = await resp.text() if 200 <= resp.status < 300 else ""

                await graceful_shutdown(protocol)

                return ProxyHttpResult(time=duration, status=resp.status, text=body)

    except (
        aiohttp.client_exceptions.ClientError,
        aiohttp.client_exceptions.ClientConnectorCertificateError,
        aiohttp.client_exceptions.ClientConnectorSSLError,
    ):
        pass
    except (  # author of aiohttp_socks did not bother with proper exception wrapping
        ProxyConnectionError,
        ProxyError,
        OSError,
        asyncio.exceptions.IncompleteReadError,
    ):
        pass
    except Exception as exc:  # noqa: BLE001
        print([proxy_url, exc])

    await graceful_shutdown(protocol)
    return None


def validate_aws_response(address: IPv4Address | IPv6Address, response: ProxyHttpResult) -> bool:
    """
    Validate the response from AWS IP check against the expected proxy IP address.

    Args:
        address (IPv4Address | IPv6Address): The proxy's IP address.
        response (ProxyHttpResult): The HTTP response object.

    Returns:
        bool: True if the IP address matches the expected value, False otherwise.
    """
    if response.status != HTTP_STATUS_OK:
        return False
    try:
        remote_address = ip_address(response.text.strip("\r\n"))
    except ValueError:
        return False
    return address == remote_address


async def check_proxy_with_aws(
    address: IPv4Address | IPv6Address,
    port: int,
    protocol: Protocol,
    login: str | None = None,
    password: str | None = None,
    delay: int = 5,
) -> tuple[bool, int]:
    """
    Check if a proxy is functional and stable using AWS IP check.

    Performs two requests with a delay in between to verify stability.

    Args:
        address (IPv4Address | IPv6Address): The IP address of the proxy.
        port (int): The port number of the proxy.
        protocol (Protocol): The proxy protocol.
        login (str, optional): Proxy login. Defaults to None.
        password (str, optional): Proxy password. Defaults to None.
        delay (int, optional): Delay between two requests in seconds. Defaults to 5.

    Returns:
        tuple[bool, int]: Tuple where first value is success status,
        and second is the latency in milliseconds.
    """
    url = "https://checkip.amazonaws.com/"

    proxy_url = format_proxy_url(address, port, protocol, login, password)

    response = await try_http_call_with_proxy(url, proxy_url, protocol)
    if not response or not validate_aws_response(address, response):
        return (False, 0)

    await asyncio.sleep(delay)  # delay between two requests to ensure proxy stability

    response = await try_http_call_with_proxy(url, proxy_url, protocol)
    if not response or not validate_aws_response(address, response):
        return (False, 0)

    return (True, response.time)


async def check_single_proxy(proxy: Proxy) -> Proxy:
    """
    Test a single proxy and updates its health status.

    Increments the attempt count and failure count if the test fails.
    Updates latency and last tested timestamp on success.

    Args:
        proxy (Proxy): The proxy instance to be tested.

    Returns:
        Proxy: The updated proxy instance with new health data.
    """
    success, response_time = await check_proxy_with_aws(
        address=proxy.address,
        port=proxy.port,
        protocol=proxy.protocol,
        login=proxy.login,
        password=proxy.password,
    )

    proxy.health.total_conn_attemps += 1

    if success:
        proxy.health.latency = response_time
        proxy.health.last_tested = datetime.datetime.now(tz=datetime.UTC)
    else:
        proxy.health.failed_conn_attemps += 1

    return proxy


async def check_proxies() -> None:
    """
    Retrieve unchecked proxies from the database, test them, and update their health.

    Proxies are tested concurrently and their updated health data is saved
    back to the database using the ProxyService.
    """
    session_factory = create_session_factory()

    proxy_service = ProxyService(SQLUnitOfWork(session_factory, raise_exc=False))

    proxies = await proxy_service.get_proxies(sort_by_unchecked=True)

    tasks = [check_single_proxy(proxy) for proxy in proxies]

    values = await asyncio.gather(*tasks, return_exceptions=True)
    # TODO(sny): one single commit
    for proxy in values:
        if isinstance(proxy, BaseException):
            continue
        await proxy_service.update(proxy)
