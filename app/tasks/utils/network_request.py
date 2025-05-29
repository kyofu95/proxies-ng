import asyncio
import logging
from typing import NamedTuple

import aiohttp
import aiohttp.client_exceptions
from aiohttp_socks import ProxyConnectionError, ProxyConnector, ProxyError

from app.models.proxy import Protocol

HTTP_STATUS_OK = 200
HTTP_STATUS_MULTIPLE_CHOICES = 300

logger = logging.getLogger(__name__)


class HttpResult(NamedTuple):
    """
    Represent the result of a direct HTTP request.

    Attributes:
        status (int): HTTP response status code.
        text (str): Response body text if status is 2xx; otherwise empty string.
    """

    status: int
    text: str


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


async def graceful_shutdown(protocol: Protocol | None = None) -> None:
    """
    Ensure graceful shutdown of the aiohttp connection.

    For HTTPS, waits briefly to allow SSL connections to close properly.
    Refer to aiohttp docs:
    https://docs.aiohttp.org/en/stable/client_advanced.html#graceful-shutdown

    Args:
        protocol (Protocol): The protocol used by the proxy.
    """
    if protocol and protocol == Protocol.HTTPS:
        # Wait 250 ms for the underlying SSL connections to close
        await asyncio.sleep(0.250)
    else:
        # Zero-sleep to allow underlying connections to close
        await asyncio.sleep(0)


async def try_http_request_with_proxy(
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
        proxy_url (str): The proxy server URL in format protocol://ip:port.
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
                body = ""
                if HTTP_STATUS_OK <= resp.status < HTTP_STATUS_MULTIPLE_CHOICES:
                    body = await resp.text()

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
    except Exception:  # noqa: BLE001
        logger.debug("Proxy check failed for %s", proxy_url, exc_info=True)

    await graceful_shutdown(protocol)
    return None


async def try_http_request(url: str) -> HttpResult | None:
    """
    Attempt a direct HTTP GET request and returns the result.

    Automatically follows redirects up to a limit.

    Args:
        url (str): The target URL for the HTTP GET request.

    Returns:
        HttpResult | None: Result containing status and text if successful; None otherwise.
    """
    try:
        async with aiohttp.ClientSession() as session:
            response = await session.get(url, allow_redirects=True, max_redirects=10)
            body = ""
            if HTTP_STATUS_OK <= response.status < HTTP_STATUS_MULTIPLE_CHOICES:
                body = await response.text()

            await graceful_shutdown()

            return HttpResult(status=response.status, text=body)
    except (aiohttp.client_exceptions.ClientError, ConnectionError) as exc:
        logger.debug("Http request to '%s' failed", url, exc_info=exc)

    return None
