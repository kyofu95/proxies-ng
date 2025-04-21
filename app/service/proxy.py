from datetime import datetime
from ipaddress import IPv4Address, IPv6Address
from typing import Any, NamedTuple
from uuid import UUID, uuid4

import pycountry

from app.core.exceptions import CountryCodeError, NotFoundError
from app.core.uow import SQLUnitOfWork
from app.models.proxy import Location, Protocol, Proxy, ProxyAddress, ProxyHealth


class InitialHealth(NamedTuple):
    """
    Represent the initial health status of a proxy.

    Attributes:
        latency (int): Measured latency in milliseconds.
        tested (datetime): The timestamp when the proxy was tested.
    """

    latency: int
    tested: datetime


class ProxyService:
    """
    Service layer for managing proxy entities.

    This class provides methods for creating, retrieving, updating,
    and deleting proxy records using the repository pattern.
    """

    def __init__(self, uow: SQLUnitOfWork) -> None:
        """
        Initialize the ProxyService with a given async session.

        Args:
            uow (SQLUnitOfWork): The unit-of-work instance.
        """
        self.uow = uow

    async def create(
        self,
        address: IPv4Address | IPv6Address,
        port: int,
        protocol: Protocol,
        login: str | None = None,
        password: str | None = None,
        location: Location | None = None,
    ) -> Proxy:
        """
        Create and persist a new proxy entity.

        Args:
            address (IPv4Address | IPv6Address): The IP address of the proxy.
            port (int): The port number of the proxy.
            protocol (Protocol): The protocol type of the proxy.
            login (str | None): The login credential (if applicable). Defaults to None.
            password (str | None): The password credential (if applicable). Defaults to None.
            location (Location | None): Optional geolocation data associated with the proxy. Defaults to None.

        Returns:
            Proxy: The newly created and persisted proxy entity.
        """
        proxy = await self._build(
            address=address,
            port=port,
            protocol=protocol,
            login=login,
            password=password,
            location=location,
        )

        async with self.uow as uow:
            return await uow.proxy_repository.add(proxy)

    async def create_bulk(self, proxies_data: list[dict[str, Any]]) -> None:
        """
        Create and persist multiple proxy entities.

        Args:
            proxies_data (list[dict[str, Any]]): A list of dictionaries containing the data for each proxy entity.
        """
        proxies: list[Proxy] = []

        for data in proxies_data:
            proxy = await self._build(
                address=data["address"],
                port=data["port"],
                protocol=data["protocol"],
                login=data.get("login", None),
                password=data.get("password", None),
                location=data.get("location", None),
                initial_health=data.get("initial_health", None),
            )
            proxies.append(proxy)

        async with self.uow as uow:
            await uow.proxy_repository.add_bulk(proxies)

    async def get_by_id(self, id_: UUID) -> Proxy | None:
        """
        Retrieve a proxy entity by its unique identifier.

        Args:
            id_ (UUID): The unique identifier of the proxy.

        Returns:
            Proxy | None: The retrieved proxy entity or None if not found.
        """
        async with self.uow as uow:
            return await uow.proxy_repository.get_by_id(id_)

    async def update(self, proxy: Proxy) -> Proxy:
        """
        Update an existing proxy entity.

        Args:
            proxy (Proxy): The proxy entity with updated data.

        Returns:
            Proxy: The updated proxy entity.
        """
        async with self.uow as uow:
            return await uow.proxy_repository.update(proxy)

    async def remove(self, proxy: Proxy) -> None:
        """
        Remove a proxy entity from the database.

        Args:
            proxy (Proxy): The proxy entity to be removed.
        """
        async with self.uow as uow:
            await uow.proxy_repository.remove(proxy)

    async def get_proxies(
        self,
        protocol: Protocol | None = None,
        country_alpha2_code: str | None = None,
        *,
        only_checked: bool = False,
        offset: int | None = None,
        limit: int | None = None,
        sort_by_unchecked: bool = False,
    ) -> list[Proxy]:
        """
        Retrieve a list of proxies filtered by protocol and/or country. Omits proxies without geoaddress.

        Args:
            protocol (Protocol | None, optional): The protocol to filter proxies by. Defaults to None.
            country_alpha2_code (str | None, optional): The country code in 3166-1 Alpha-2 format to
                filter proxies by. Defaults to None.
            only_checked (bool): Get only verified proxies. Defaults to False.
            offset (int | None, optional): Number of proxies to skip (used for pagination). Defaults to None.
            limit (int | None, optional): Maximum number of proxies to return. Defaults to None.
            sort_by_unchecked (bool): If True, sort proxies with no 'last_tested' first.
                Cannot be True when 'only_checked' is also True.

        Raises:
            ValueError: If both 'only_checked' and 'sort_by_unchecked' are True.

        Returns:
            list[Proxy]: A list of Proxy entities that match the given filters.
        """
        if only_checked and sort_by_unchecked:
            raise ValueError("Cannot sort by unchecked if only_checked is True")

        # validate country code
        if country_alpha2_code and not pycountry.countries.get(alpha_2=country_alpha2_code):
            message = f"Unknown country code: {country_alpha2_code}"
            raise CountryCodeError(message)

        async with self.uow as uow:
            return await uow.proxy_repository.get_proxies(
                protocol=protocol,
                country_alpha2_code=country_alpha2_code,
                only_checked=only_checked,
                offset=offset,
                limit=limit,
                sort_by_unchecked=sort_by_unchecked,
            )

    async def get_proxies_count(
        self,
        protocol: Protocol | None = None,
        country_alpha2_code: str | None = None,
        *,
        only_checked: bool = False,
    ) -> int:
        """
        Count the number of proxies that match the given filters.

        Delegates the counting logic to the proxy repository, using the configured unit of work.

        Args:
            protocol (Protocol | None): Optional protocol to filter proxies by.
            country_alpha2_code (str | None): Optional ISO 3166-1 Alpha-2 country code to filter proxies by.
            only_checked (bool): If True, count only proxies that have been tested. Defaults to False.

        Returns:
            int: The number of proxies matching the specified filters.
        """
        async with self.uow as uow:
            return await uow.proxy_repository.get_proxies_count(
                protocol=protocol,
                country_alpha2_code=country_alpha2_code,
                only_checked=only_checked,
            )

    async def get_countries(self) -> list[str]:
        """
        Retrieve a list of distinct country codes associated with proxies.

        Returns:
            list[str]: A list of ISO 3166-1 alpha-2 country codes.
        """
        async with self.uow as uow:
            return await uow.proxy_repository.get_countries()

    async def _build(
        self,
        address: IPv4Address | IPv6Address,
        port: int,
        protocol: Protocol,
        login: str | None = None,
        password: str | None = None,
        location: Location | None = None,
        initial_health: InitialHealth | None = None,
    ) -> Proxy:
        """
        Build a new Proxy entity with its associated health and location data.

        Args:
            address (IPv4Address | IPv6Address): The IP address of the proxy.
            port (int): The port number of the proxy.
            protocol (Protocol): The protocol type of the proxy.
            login (str | None): The login credential (if applicable). Defaults to None.
            password (str | None): The password credential (if applicable). Defaults to None.
            location (Location | None): Optional geolocation data associated with the proxy. Defaults to None.
            initial_health (InitialHealth | None, optional): Optional initial health metrics for the proxy.
                Defaults to None.

        Returns:
            Proxy: The constructed Proxy entity with associated health and geo location.
        """
        proxy = Proxy()
        proxy.id = uuid4()
        proxy.address = address
        proxy.port = port
        proxy.protocol = protocol
        proxy.login = login
        proxy.password = password

        proxy.health = ProxyHealth()
        proxy.health.id = uuid4()
        proxy.health.total_conn_attemps = 0
        proxy.health.failed_conn_attemps = 0
        proxy.health.latency = 0
        proxy.health.last_tested = None
        proxy.health.proxy_id = proxy.id

        if initial_health:
            proxy.health.total_conn_attemps = 1
            proxy.health.latency = initial_health.latency
            proxy.health.last_tested = initial_health.tested

        proxy.geo_address = await self._resolve_location(location) if location else None

        if proxy.geo_address:
            proxy.geo_address_id = proxy.geo_address.id

        return proxy

    async def _resolve_location(self, location: Location) -> ProxyAddress:
        """
        Resolve the location to a ProxyAddress entity, or create a new address if not found.

        Args:
            location (Location): The location data (country, region, city) to resolve.

        Returns:
            ProxyAddress: The resolved or newly created ProxyAddress entity.
        """
        async with self.uow as uow:
            geo_address = await uow.proxy_repository.get_geo_address_by_location(
                location.country_code,
                location.region,
                location.city,
            )
            if not geo_address:
                country = await uow.proxy_repository.get_country_by_code(location.country_code)
                if not country:
                    message = f"Could not find country with code {location.country_code}"
                    raise NotFoundError(message)

                geo_address = ProxyAddress()
                geo_address.id = uuid4()
                geo_address.city = location.city
                geo_address.region = location.region
                geo_address.country = country
                geo_address.country_id = geo_address.country.id
                geo_address = await uow.proxy_repository.add_geo_address(geo_address)
            return geo_address
