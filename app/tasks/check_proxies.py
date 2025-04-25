import asyncio
import datetime
import logging
from ipaddress import IPv4Address, IPv6Address, ip_address

from app.core.database import create_session_factory
from app.core.uow import SQLUnitOfWork
from app.models.proxy import Protocol, Proxy
from app.service.proxy import ProxyService

from .utils.network_request import HTTP_STATUS_OK, ProxyHttpResult, try_http_request_with_proxy

logger = logging.getLogger(__name__)


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

    response = await try_http_request_with_proxy(url, proxy_url, protocol)
    if not response or not validate_aws_response(address, response):
        return (False, 0)

    await asyncio.sleep(delay)  # delay between two requests to ensure proxy stability

    response = await try_http_request_with_proxy(url, proxy_url, protocol)
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

    # filter out exceptions
    checked_proxies = [proxy for proxy in values if not isinstance(proxy, BaseException)]

    # TODO(sny): one single commit
    for proxy in checked_proxies:
        await proxy_service.update(proxy)
