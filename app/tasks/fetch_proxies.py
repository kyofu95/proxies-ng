from ipaddress import IPv4Address, IPv6Address, ip_address
from typing import Any

import aiohttp
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.database import create_session_factory
from app.core.geoip import GeoIP
from app.core.uow import SQLUnitOfWork
from app.models.proxy import Protocol
from app.service.proxy import ProxyService

type IPAddress = IPv4Address | IPv6Address
type RawProxyTuple = tuple[IPAddress, int]

HTTP_STATUS_OK = 200

PORT_RANGE_START = 1
PORT_RANGE_END = 65535


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


def try_parse_ip_port(ip_str: str, port_str: str) -> tuple[IPAddress, int] | None:
    """
    Attempt to parse an IP and port from strings.

    Args:
        ip_str (str): IP address as a string.
        port_str (str): Port as a string.

    Returns:
        tuple[IPAddress, int] | None: A tuple of IP address and port if valid, otherwise None.
    """
    try:
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
        response = await session.get(url)
        if response.status != HTTP_STATUS_OK:
            return None

        data = await response.text()

    proxies: list[RawProxyTuple] = []

    lines = data.splitlines()
    for line in lines:
        ip_str, port_str = line.split(sep=":")
        parse_result = try_parse_ip_port(ip_str, port_str)
        if not parse_result:
            continue

        proxies.append(parse_result)

    return proxies


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

    geoip_service = GeoIP(databasefile="geoip/GeoLite2-City.mmdb")

    proxy_service = ProxyService(SQLUnitOfWork(session_factory, raise_exc=False))

    proxies: list[dict[str, Any]] = []

    for ip, port in raw_proxies:
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
            },
        )

    await proxy_service.create_bulk(proxies)


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
