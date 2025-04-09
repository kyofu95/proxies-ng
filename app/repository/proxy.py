from uuid import UUID

from sqlalchemy import and_, insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AlreadyExistsError, NotFoundError
from app.models.proxy import Protocol, Proxy, ProxyAddress, ProxyHealth

from .base import BaseRepository


class ProxyRepository(BaseRepository[Proxy]):
    """
    Repository for handling database operations related to the Proxy model.

    Attributes:
        session (AsyncSession): The async database session.
    """

    def __init__(self, async_session: AsyncSession) -> None:
        """
        Initialize the repository with an async session.

        Args:
            async_session (AsyncSession): The async database session.
        """
        self.session = async_session

    async def add(self, entity: Proxy) -> Proxy:
        """
        Add a new Proxy entity to the database.

        Args:
            entity (Proxy): The Proxy entity to add.

        Returns:
            Proxy: The added Proxy entity.
        """
        self.session.add(entity)
        return entity

    async def get_by_id(self, id_: UUID) -> Proxy | None:
        """
        Retrieve a Proxy by its ID.

        Args:
            id_ (UUID): The ID of the Proxy entity.

        Returns:
            Proxy | None: The Proxy entity if found, otherwise None.
        """
        return await self.session.get(Proxy, id_)

    async def update(self, entity: Proxy) -> Proxy:
        """
        Update an existing Proxy entity in the database.

        Args:
            entity (Proxy): The Proxy entity to update.

        Raises:
            NotFoundError: If the entity does not exist in the database.

        Returns:
            Proxy: The updated Proxy entity.
        """
        stored_entity = await self.session.get(Proxy, entity.id)
        if not stored_entity:
            raise NotFoundError(
                "Entity has not been stored in database, but were marked for update.",
            )

        await self.session.flush([entity])

        return entity

    async def remove(self, entity: Proxy) -> None:
        """
        Remove a Proxy entity from the database.

        Args:
            entity (Proxy): The Proxy entity to remove.
        """
        await self.session.delete(entity)

    async def add_geo_address(
        self,
        geo_address: ProxyAddress,
    ) -> ProxyAddress:
        """
        Add a new ProxyAddress entity to the database.

        If the address already exists, an AlreadyExistsError is raised.

        Args:
            geo_address (ProxyAddress): The ProxyAddress entity to add.

        Raises:
            AlreadyExistsError: If the address already exists.

        Returns:
            ProxyAddress: The added ProxyAddress entity.
        """
        address = await self.get_geo_address_by_location(
            geo_address.country,
            geo_address.region,
            geo_address.city,
        )
        if address:
            raise AlreadyExistsError("Address already exists")

        # insert, since it doesn't exists
        stmt = (
            insert(ProxyAddress)
            .values(
                id=geo_address.id,
                country=geo_address.country,
                region=geo_address.region,
                city=geo_address.city,
            )
            .returning(ProxyAddress)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def get_geo_address_by_id(self, id_: UUID) -> ProxyAddress | None:
        """
        Retrieve a ProxyAddress by its ID.

        Args:
            id_ (UUID): The ID of the ProxyAddress entity.

        Returns:
            ProxyAddress | None: The ProxyAddress entity if found, otherwise None.
        """
        stmt = select(ProxyAddress).where(ProxyAddress.id == id_)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_geo_address_by_location(
        self,
        country: str,
        region: str,
        city: str,
    ) -> ProxyAddress | None:
        """
        Retrieve a ProxyAddress by its country, region, and city.

        Args:
            country (str): The country of the ProxyAddress.
            region (str): The region of the ProxyAddress.
            city (str): The city of the ProxyAddress.

        Returns:
            ProxyAddress | None: The ProxyAddress entity if found, otherwise None.
        """
        stmt = select(ProxyAddress).where(
            and_(
                ProxyAddress.country == country,
                ProxyAddress.region == region,
                ProxyAddress.city == city,
            ),
        )

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_proxies(
        self,
        protocol: Protocol | None = None,
        country: str | None = None,
        *,
        only_checked: bool = False,
        limit: int | None = None,
        sort_by_unchecked: bool = False,
    ) -> list[Proxy]:
        """
        Retrieve a list of Proxy entities with optional filtering and sorting.

        By default, only proxies with a non-null geo_address are returned.
        You can further filter by protocol and country, and limit results.
        If 'only_checked' is True, returns only proxies that have been tested at least once.
        If 'sort_by_unchecked' is True, returns proxies sorted by null 'last_tested' first.

        Args:
            protocol (Protocol | None): Optional protocol to filter proxies by.
            country (str | None): Optional country to filter proxies by (requires associated geo address).
            only_checked (bool): If True, include only proxies that were tested. Defaults to False.
            limit (int | None): Optional limit on the number of proxies returned.
            sort_by_unchecked (bool): If True, sort proxies with no 'last_tested' first.
                Cannot be True when 'only_checked' is also True.

        Raises:
            ValueError: If both 'only_checked' and 'sort_by_unchecked' are True.

        Returns:
            list[Proxy]: A list of Proxy entities matching the provided filters.
        """
        if only_checked and sort_by_unchecked:
            raise ValueError("Cannot sort by unchecked if only_checked is True")

        stmt = select(Proxy).where(Proxy.geo_address_id.isnot(None))

        if protocol:
            stmt = stmt.where(Proxy.protocol == protocol)

        if country:
            stmt = stmt.join(ProxyAddress).where(ProxyAddress.country == country)

        stmt = stmt.join(ProxyHealth)
        if only_checked:
            stmt = stmt.where(and_(ProxyHealth.last_tested.is_not(None), ProxyHealth.total_conn_attemps > 0))

            # Descending order means latest proxy on the top
            stmt = stmt.order_by(ProxyHealth.last_tested.desc())

        if sort_by_unchecked:
            stmt = stmt.order_by(ProxyHealth.last_tested.asc().nulls_first())

        if limit:
            stmt = stmt.limit(limit)

        result = await self.session.execute(stmt)

        return list(result.scalars().all())
