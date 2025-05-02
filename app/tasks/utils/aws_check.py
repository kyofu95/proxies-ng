import asyncio
from ipaddress import IPv4Address, IPv6Address, ip_address

from app.models.proxy import Protocol

from .network_request import HTTP_STATUS_OK, ProxyHttpResult, try_http_request_with_proxy


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


async def try_aws_http_request_with_proxy(
    address: IPv4Address | IPv6Address,
    url: str,
    proxy_url: str,
    protocol: Protocol,
) -> tuple[bool, int]:
    """
    Attempt a single HTTP request through a proxy and validate it via AWS IP check.

    This function sends a request to the given URL through the proxy and verifies
    whether the response matches the proxy's IP address.

    Args:
        address (IPv4Address | IPv6Address): The expected IP address of the proxy.
        url (str): The URL to request (e.g., AWS IP check URL).
        proxy_url (str): The full formatted proxy URL.
        protocol (Protocol): The protocol used by the proxy.

    Returns:
        tuple[bool, int]: A tuple containing a success flag and the response time in milliseconds.
    """
    response = await try_http_request_with_proxy(url, proxy_url, protocol)
    if not response or not validate_aws_response(address, response):
        return (False, 0)
    return (True, response.time)


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

    response = await try_aws_http_request_with_proxy(address, url, proxy_url, protocol)
    if not response[0]:
        return (False, 0)

    await asyncio.sleep(delay)  # delay between two requests to ensure proxy stability

    response = await try_aws_http_request_with_proxy(address, url, proxy_url, protocol)
    if not response[0]:
        return (False, 0)

    return (True, response[1])
