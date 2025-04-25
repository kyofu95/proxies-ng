import asyncio
import datetime
import logging
from ipaddress import IPv4Address, IPv6Address, ip_address
from typing import Any

import aiohttp
import aiohttp.client_exceptions

from app.core.database import create_session_factory
from app.core.geoip import GeoIP
from app.core.uow import SQLUnitOfWork
from app.models.proxy import Protocol
from app.models.source import Source
from app.service.proxy import InitialHealth, ProxyService

from .check_proxies import check_proxy_with_aws

type IPAddress = IPv4Address | IPv6Address

HTTP_STATUS_OK = 200

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

        if parts_length == 2:
            ip_str, port_str = substrings
        elif parts_length == 3:
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
    try:
        async with aiohttp.ClientSession() as session:
            response = await session.get(url, allow_redirects=True, max_redirects=10)
            if response.status != HTTP_STATUS_OK:
                log_msg = f"Http request on url '{url}' responded with {response.status}"
                logger.debug(log_msg)
                return None

            data = await response.text()
            if not data:
                logger.debug("Http request OK, but no data were attached")
                return None
    except aiohttp.client_exceptions.ClientError as exc:
        msg = f"Http request to {url} failed"
        logger.debug(msg, exc_info=exc)

    proxies: list[tuple[IPAddress, int, Protocol]] = []

    lines = data.splitlines()
    for line in lines:
        parse_result = try_parse_ip_port(line)
        if not parse_result:
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


async def fetch_all_proxy_lists(sources: list[Source]) -> list[tuple[IPAddress, int, Protocol]]:
    """
    Fetch proxy lists from all provided sources and parses them.

    Args:
        sources (list[Source]): List of proxy sources to fetch from.

    Returns:
        list[tuple[IPAddress, int, Protocol]]: A list of all parsed proxies from all sources.
    """
    unchecked_proxies: list[tuple[IPAddress, int, Protocol]] = []

    fetch_tasks = [
        download_proxy_list(source.uri, source.uri_predefined_type) for source in sources if source.uri_predefined_type
    ]

    fetch_tasks_results = await asyncio.gather(*fetch_tasks, return_exceptions=True)

    # process list of lists to list
    for proxy_list in fetch_tasks_results:
        if not proxy_list or isinstance(proxy_list, BaseException):
            continue
        unchecked_proxies.extend(proxy_list)

    return unchecked_proxies


async def check_list_of_proxies(
    proxies: list[tuple[IPv4Address | IPv6Address, int, Protocol]],
) -> list[tuple[IPv4Address | IPv6Address, int, Protocol, int, datetime.datetime]]:
    """
    Asynchronously check a list of proxies for availability and latency.

    Args:
        proxies (list[tuple[IPAddress, int, Protocol]]): A list of proxies to check.

    Returns:
        list[tuple[IPAddress, int, Protocol, int, datetime.datetime]]:
            A list of successfully validated proxies with latency and test time.
    """
    check_tasks = [check_proxy((proxy[0], proxy[1]), proxy[2]) for proxy in proxies]
    check_tasks_results = await asyncio.gather(*check_tasks, return_exceptions=True)
    return [proxy for proxy in check_tasks_results if proxy and not isinstance(proxy, BaseException)]


async def fetch_proxies() -> None:
    """
    Fetch and store proxies from all predefined proxy sources in the database.

    This function:
    - Fetches all proxy sources from the database.
    - Downloads proxy lists from each source.
    - Validates each proxy via AWS checks.
    - Enriches valid proxies with geolocation.
    - Persists valid and public proxies in bulk.
    """
    # TODO(sny): split function into smaller functions
    session_factory = create_session_factory()

    async with SQLUnitOfWork(session_factory) as uow:
        sources = await uow.source_repository.get_all()

    if not sources:
        return

    geoip_service = GeoIP(databasefile="geoip/GeoLite2-City.mmdb")

    unchecked_proxies = await fetch_all_proxy_lists(sources)
    if not unchecked_proxies:
        return

    proxy_service = ProxyService(SQLUnitOfWork(session_factory, raise_exc=False))

    chunk_size = 500
    for i in range(0, len(unchecked_proxies), chunk_size):
        chunk = unchecked_proxies[i : i + chunk_size]
        checked_proxies = await check_list_of_proxies(chunk)
        if not checked_proxies:
            continue

        proxies: list[dict[str, Any]] = []

        for ip, port, protocol, latency, last_tested in checked_proxies:
            # we need only public ip's
            if not ip.is_global:
                continue

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

        await proxy_service.create_bulk(proxies)
