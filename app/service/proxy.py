from ipaddress import IPv4Address, IPv6Address
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.proxy import Protocol, Proxy, ProxyHealth
from app.repository.proxy import ProxyRepository


class ProxyService:
    """
    Service layer for managing proxy entities.

    This class provides methods for creating, retrieving, updating,
    and deleting proxy records using the repository pattern.
    """

    def __init__(self, async_session: AsyncSession) -> None:
        """
        Initialize the ProxyService with a given async session.

        Args:
            async_session (AsyncSession): The asynchronous session for database operations.
        """
        self.proxy_repository = ProxyRepository(async_session)

    async def create(
        self,
        address: IPv4Address | IPv6Address,
        port: int,
        protocol: Protocol,
        login: str | None = None,
        password: str | None = None,
    ) -> Proxy:
        """
        Create and persist a new proxy entity.

        Args:
            address (IPv4Address | IPv6Address): The IP address of the proxy.
            port (int): The port number of the proxy.
            protocol (Protocol): The protocol type of the proxy.
            login (str | None): The login credential (if applicable). Defaults to None.
            password (str | None): The password credential (if applicable). Defaults to None.

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
        proxy.geo_address = None

        return await self.proxy_repository.add(proxy)

    async def get_by_id(self, id_: UUID) -> Proxy | None:
        """
        Retrieve a proxy entity by its unique identifier.

        Args:
            id_ (UUID): The unique identifier of the proxy.

        Returns:
            Proxy | None: The retrieved proxy entity or None if not found.
        """
        return await self.proxy_repository.get_by_id(id_)

    async def update(self, proxy: Proxy) -> Proxy:
        """
        Update an existing proxy entity.

        Args:
            proxy (Proxy): The proxy entity with updated data.

        Returns:
            Proxy: The updated proxy entity.
        """
        return await self.proxy_repository.update(proxy)

    async def remove(self, proxy: Proxy) -> None:
        """
        Remove a proxy entity from the database.

        Args:
            proxy (Proxy): The proxy entity to be removed.
        """
        await self.proxy_repository.remove(proxy)
