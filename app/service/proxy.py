from ipaddress import IPv4Address, IPv6Address
from uuid import UUID, uuid4

from app.core.uow import SQLUnitOfWork
from app.models.proxy import Location, Protocol, Proxy, ProxyAddress, ProxyHealth


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
        proxy = Proxy()
        proxy.id = uuid4()
        proxy.address = address
        proxy.port = port
        proxy.protocol = protocol
        proxy.login = login
        proxy.password = password

        proxy_health = ProxyHealth()
        proxy_health.id = uuid4()
        proxy_health.total_conn_attemps = 0
        proxy_health.failed_conn_attemps = 0

        proxy.health = proxy_health

        async with self.uow as uow:
            if location:
                geo_address = await uow.proxy_repository.get_geo_address_by_location(
                    location.country,
                    location.region,
                    location.city,
                )
                if not geo_address:
                    geo_address = ProxyAddress()
                    geo_address.id = uuid4()
                    geo_address.city = location.city
                    geo_address.region = location.region
                    geo_address.country = location.country
                    geo_address = await uow.proxy_repository.add_geo_address(geo_address)
                proxy.geo_address = geo_address
            else:
                proxy.geo_address = None

            return await uow.proxy_repository.add(proxy)

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
        country: str | None = None,
        *,
        only_checked: bool = False,
    ) -> list[Proxy]:
        """
        Retrieve a list of proxies filtered by protocol and/or country. Omits proxies without geoaddress.

        Args:
            protocol (Protocol | None, optional): The protocol to filter proxies by. Defaults to None.
            country (str | None, optional): The country to filter proxies by. Defaults to None.
            only_checked (bool): Get only verified proxies. Defaults no False.

        Returns:
            list[Proxy]: A list of Proxy entities that match the given filters.
        """
        async with self.uow as uow:
            return await uow.proxy_repository.get_proxies(
                protocol=protocol,
                country=country,
                only_checked=only_checked,
            )
