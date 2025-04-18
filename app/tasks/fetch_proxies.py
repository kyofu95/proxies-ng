import asyncio
import datetime
import logging
from ipaddress import IPv4Address, IPv6Address, ip_address
from typing import Any

import aiohttp
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.database import create_session_factory
from app.core.geoip import GeoIP
from app.core.uow import SQLUnitOfWork
from app.models.proxy import Protocol
from app.service.proxy import InitialHealth, ProxyService

from .check_proxies import check_proxy_with_aws

type IPAddress = IPv4Address | IPv6Address
type RawProxyTuple = tuple[IPAddress, int]

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


async def download_proxy_list(url: str) -> list[RawProxyTuple] | None:
    """
    Download and parse a list of proxy addresses from a given URL.

    The URL is expected to return proxies in the format "IP:PORT" per line.

    Args:
        url (str): The URL to download the proxy list from.

    Returns:
        list[RawProxyTuple] | None: A list of parsed (IP, port) tuples or None on failure.
    """
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

    proxies: list[RawProxyTuple] = []

    lines = data.splitlines()
    for line in lines:
        parse_result = try_parse_ip_port(line)
        if not parse_result:
            continue

        proxies.append(parse_result)

    return proxies


async def check_proxy(
    raw_proxy: RawProxyTuple,
    protocol: Protocol,
) -> tuple[IPv4Address | IPv6Address, int, int, datetime.datetime] | None:
    """
    Check the validity of a proxy by testing its connectivity and latency using AWS.

    Args:
        raw_proxy (RawProxyTuple): A tuple of (IP address, port) representing the proxy.
        protocol (Protocol): The protocol to use for checking the proxy (e.g., HTTP, SOCKS5).

    Returns:
        tuple[IPv4Address | IPv6Address, int, int, datetime.datetime] | None:
            A tuple containing the proxy's IP address, port, latency (ms), and the current time
            when the test was conducted. Returns None if the proxy is invalid.
    """
    success, latency = await check_proxy_with_aws(raw_proxy[0], raw_proxy[1], protocol)
    if success:
        return (raw_proxy[0], raw_proxy[1], latency, datetime.datetime.now(tz=datetime.UTC))
    return None


async def fetch_proxies_task(url: str, protocol: Protocol, session_factory: async_sessionmaker[AsyncSession]) -> None:
    """
    Download proxies from a given URL, enrich them with geolocation, and save to the database.

    Args:
        url (str): The URL to fetch the proxies from.
        protocol (Protocol): The protocol to associate with the proxies (e.g., HTTP, SOCKS5).
        session_factory (async_sessionmaker[AsyncSession]): The session factory for creating database sessions.
    """
    raw_proxies = await download_proxy_list(url)
    if not raw_proxies:
        return

    # we need only public ip's
    raw_proxies = [proxy for proxy in raw_proxies if not proxy[0].is_private and not proxy[0].is_reserved]

    tasks = [check_proxy(proxy, protocol) for proxy in raw_proxies]
    values = await asyncio.gather(*tasks, return_exceptions=True)
    checked_proxies = [proxy for proxy in values if proxy and not isinstance(proxy, BaseException)]

    geoip_service = GeoIP(databasefile="geoip/GeoLite2-City.mmdb")

    proxy_service = ProxyService(SQLUnitOfWork(session_factory, raise_exc=False))

    proxies: list[dict[str, Any]] = []

    for ip, port, latency, last_tested in checked_proxies:
        # we need only public ip's
        if ip.is_private or ip.is_reserved:
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

    # split proxies into chunks before inserting
    chunk_size = 4_000
    for chunks in [proxies[i : i + chunk_size] for i in range(0, len(proxies), chunk_size)]:
        await proxy_service.create_bulk(chunks)


async def fetch_proxies() -> None:
    """
    Fetch and store proxies from all predefined proxy sources in the database.

    This is the main task that loops through all known proxy sources and delegates
    downloading/parsing each one to "fetch_proxies_task".
    """
    session_factory = create_session_factory()

    async with SQLUnitOfWork(session_factory) as uow:
        sources = await uow.source_repository.get_all()

    for source in sources:
        if not source.uri_predefined_type:
            continue
        await fetch_proxies_task(source.uri, source.uri_predefined_type, session_factory)
