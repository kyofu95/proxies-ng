import datetime
import logging
from ipaddress import IPv4Address, IPv6Address, ip_address
from typing import Any

from app.core.database import create_session_factory
from app.core.geoip import GeoIP
from app.core.uow import SQLUnitOfWork
from app.models.proxy import Protocol
from app.models.source import Source
from app.service.proxy import InitialHealth, ProxyService
from app.service.source import SourceService

from .utils.aws_check import check_proxy_with_aws
from .utils.gather import cgather
from .utils.network_request import HTTP_STATUS_OK, try_http_request

type IPAddress = IPv4Address | IPv6Address

PORT_RANGE_START = 1
PORT_RANGE_END = 65535

logger = logging.getLogger(__name__)


def validate_port(port: int) -> None:
    """
    Validate that a given port number is within the valid TCP/UDP range.

    Args:
        port (int): The port number to validate.

    Raises:
        ValueError: If the port number is outside the valid range [1, 65535].
    """
    if not (PORT_RANGE_START <= port <= PORT_RANGE_END):
        raise ValueError("Valid port range is [1; 65535]")


SCHEME_IP_PORT_LENGTH = 2  #  ip:port
SCHEME_PROTOCOL_IOP_PORT_LENGTH = 3  #  protocol://ip:port


def try_parse_ip_port(proxy_line: str) -> tuple[IPAddress, int] | None:
    """
    Attempt to parse a proxy string in the format IP:PORT or protocol://IP:PORT.

    Supports both IPv4 and IPv6 addresses (without square brackets).

    Args:
        proxy_line (str): The proxy string to parse.

    Returns:
        tuple[IPAddress, int] | None: A tuple of (IP address, port) if parsing is successful, otherwise None.
    """
    try:
        # TODO(sny): parse IPv6 with [2001:db8::1]:8080
        substrings = proxy_line.split(":")
        parts_length = len(substrings)

        if parts_length == SCHEME_IP_PORT_LENGTH:
            ip_str, port_str = substrings
        elif parts_length == SCHEME_PROTOCOL_IOP_PORT_LENGTH:
            _, ip_str, port_str = substrings  # omit protocol
            ip_str = ip_str.lstrip("/")
        else:
            return None

        ip = ip_address(ip_str)
        port = int(port_str)
        validate_port(port)

    except ValueError:
        return None
    return (ip, port)


async def download_proxy_list(
    url: str,
    protocol: Protocol,
) -> list[tuple[IPAddress, int, Protocol]] | None:
    """
    Download a list of proxies from the given URL and parses them.

    The URL is expected to return proxies in the format "IP:PORT" or "PROTOCOL://IP:PORT" per line.

    Args:
        url (str): The URL to download the proxy list from.
        protocol (Protocol): The protocol type to associate with each proxy.

    Returns:
        list[tuple[IPAddress, int, Protocol]] | None: A list of tuples containing IP, port, and protocol.
            Returns None if the request fails or the response is invalid.
    """
    http_result = await try_http_request(url=url)
    if not http_result:
        logger.debug("Http request to '%s' failed", url)
        return None

    if http_result.status != HTTP_STATUS_OK:
        logger.debug("Http request to '%s' failed with status code %i", url, http_result.status)
        return None

    proxies: list[tuple[IPAddress, int, Protocol]] = []

    lines = http_result.text.splitlines()
    for line in lines:
        parse_result = try_parse_ip_port(line)
        if not parse_result:
            continue

        # we need only public ip's
        if not parse_result[0].is_global:
            continue

        proxies.append((*parse_result, protocol))

    return proxies


async def check_proxy(
    raw_proxy: tuple[IPAddress, int],
    protocol: Protocol,
) -> tuple[IPv4Address | IPv6Address, int, Protocol, int, datetime.datetime] | None:
    """
    Check the validity of a proxy by testing its connectivity and latency using AWS.

    Args:
        raw_proxy (tuple[IPAddress, int]): A tuple of (IP address, port) representing the proxy.
        protocol (Protocol): The protocol to use for checking the proxy (e.g., HTTP, SOCKS5).

    Returns:
        tuple[IPAddress, int, Protocol, int, datetime.datetime] | None:
            A tuple containing the IP address, port, protocol, latency in milliseconds,
            and timestamp of the test. Returns None if the proxy is invalid.
    """
    success, latency = await check_proxy_with_aws(raw_proxy[0], raw_proxy[1], protocol)
    if success:
        return (raw_proxy[0], raw_proxy[1], protocol, latency, datetime.datetime.now(tz=datetime.UTC))
    return None


async def fetch_all_proxy_lists(
    sources: list[Source],
    source_service: SourceService,
) -> list[tuple[IPAddress, int, Protocol]]:
    """
    Fetch and parse proxy lists from a set of source URLs.

    Updates each source's connection attempt statistics.

    Args:
        sources (list[Source]): List of proxy sources.
        source_service (SourceService): Service for updating source health.

    Returns:
        list[tuple[IPAddress, int, Protocol]]: Combined list of unchecked proxies.
    """
    unchecked_proxies: list[tuple[IPAddress, int, Protocol]] = []

    for source in sources:
        proxy_list_result = await download_proxy_list(source.uri, source.uri_predefined_type)

        source.health.total_conn_attempts += 1
        source.health.last_used = datetime.datetime.now(tz=datetime.timezone.utc)
        if not proxy_list_result:
            source.health.failed_conn_attempts += 1

        await source_service.update(source)

        if proxy_list_result:
            unchecked_proxies.extend(proxy_list_result)

    return unchecked_proxies


async def check_list_of_proxies(
    proxies: list[tuple[IPAddress, int, Protocol]],
) -> list[tuple[IPAddress, int, Protocol, int, datetime.datetime]]:
    """
    Asynchronously check a list of proxies for availability and latency.

    Args:
        proxies (list[tuple[IPAddress, int, Protocol]]): A list of proxies to check.

    Returns:
        list[tuple[IPAddress, int, Protocol, int, datetime.datetime]]:
            A list of successfully validated proxies with latency and test time.
    """
    check_tasks = [check_proxy((proxy[0], proxy[1]), proxy[2]) for proxy in proxies]
    return await cgather(*check_tasks, limit=50)


async def fetch_proxies() -> None:
    """
    Fetch, validate, and store publicly available proxies from various sources.

    This includes downloading raw proxy lists, validating them using AWS checks,
    determining geolocation, and saving valid entries into the database.
    """
    # TODO(sny): split function into smaller functions
    session_factory = create_session_factory()

    source_service = SourceService(SQLUnitOfWork(session_factory, raise_exc=False))

    sources = await source_service.get_sources()
    if not sources:
        logger.debug("No proxy sources were found")
        return

    unchecked_proxies = await fetch_all_proxy_lists(sources, source_service)
    if not unchecked_proxies:
        logger.debug("No valid proxies found in proxy sources")
        return

    proxy_service = ProxyService(SQLUnitOfWork(session_factory, raise_exc=False))
    geoip_service = GeoIP(databasefile="geoip/GeoLite2-City.mmdb")

    chunk_size = 500
    for i in range(0, len(unchecked_proxies), chunk_size):
        chunk = unchecked_proxies[i : i + chunk_size]
        checked_proxies = await check_list_of_proxies(chunk)
        if not checked_proxies:
            continue

        proxies: list[dict[str, Any]] = []

        for ip, port, protocol, latency, last_tested in checked_proxies:
            location = geoip_service.get_geolocation(ip)
            if not location:
                continue

            proxies.append(
                {
                    "address": ip,
                    "port": port,
                    "protocol": protocol,
                    "location": location,
                    "initial_health": InitialHealth(latency=latency, tested=last_tested),
                },
            )

        if proxies:
            await proxy_service.create_bulk(proxies)
