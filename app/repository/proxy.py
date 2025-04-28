from uuid import UUID

from sqlalchemy import and_, distinct, func, insert, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.country import Country
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

    async def add_bulk(self, proxies: list[Proxy]) -> None:
        """
        Bulk inserts multiple Proxy entities and their associated ProxyHealth records.

        Proxies that already exist (based on conflict target) will be ignored.

        Args:
            proxies (list[Proxy]): A list of Proxy entities to insert.
        """
        if not proxies:
            return

        proxy_values = [proxy.to_dict() for proxy in proxies]

        proxy_stmt = pg_insert(Proxy).values(proxy_values).on_conflict_do_nothing().returning(Proxy.id)
        result = await self.session.execute(proxy_stmt)
        inserted_ids = {row[0] for row in result.fetchall()}

        # filter health_values by only inserted proxies
        health_values = [proxy.health.to_dict() for proxy in proxies if proxy.id in inserted_ids]

        if health_values:
            health_stmt = pg_insert(ProxyHealth).values(health_values).on_conflict_do_nothing()
            await self.session.execute(health_stmt)

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
                "Entity does not exist in the database.",
            )

        await self.session.merge(entity)

        return entity

    async def update_bulk(self, entities: list[Proxy], *, only_health: bool = False) -> None:
        """
        Bulk update multiple Proxy entities and/or their associated ProxyHealth records.

        If 'only_health' is True, only the ProxyHealth records are updated.
        Otherwise, both Proxy and ProxyHealth records are updated.

        Args:
            entities (list[Proxy]): A list of Proxy entities to update.
            only_health (bool): If True, update only ProxyHealth records. Defaults to False.
        """
        if not only_health:
            proxy_values = [proxy.to_dict() for proxy in entities]

            stmt = update(Proxy)
            await self.session.execute(stmt, proxy_values)

        proxy_health_values = [proxy.health.to_dict() for proxy in entities]

        stmt = update(ProxyHealth)
        await self.session.execute(stmt, proxy_health_values)

    async def remove(self, entity: Proxy) -> None:
        """
        Remove a Proxy entity from the database.

        Args:
            entity (Proxy): The Proxy entity to remove.
        """
        await self.session.delete(entity)

    async def get_country_by_code(self, code: str) -> Country | None:
        """
        Retrieve a Country entity by its ISO 3166-1 alpha-2 code.

        Args:
            code (str): The country code.

        Returns:
            Country | None: The Country entity if found, otherwise None.
        """
        stmt = select(Country).where(Country.code == code)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def add_geo_address(
        self,
        geo_address: ProxyAddress,
    ) -> ProxyAddress:
        """
        Add a new ProxyAddress entity to the database.

        Args:
            geo_address (ProxyAddress): The ProxyAddress entity to add.

        Returns:
            ProxyAddress: The added ProxyAddress entity.
        """
        stmt = (
            insert(ProxyAddress)
            .values(
                id=geo_address.id,
                country_id=geo_address.country_id,
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
        country_alpha2_code: str,
        region: str,
        city: str,
    ) -> ProxyAddress | None:
        """
        Retrieve a ProxyAddress by its country, region, and city.

        Args:
            country_alpha2_code (str): The country code of the ProxyAddress in 3166-1 Alpha-2 format.
            region (str): The region of the ProxyAddress.
            city (str): The city of the ProxyAddress.

        Returns:
            ProxyAddress | None: The ProxyAddress entity if found, otherwise None.
        """
        stmt = (
            select(ProxyAddress)
            .where(
                and_(
                    ProxyAddress.region == region,
                    ProxyAddress.city == city,
                ),
            )
            .join(Country)
            .where(Country.code == country_alpha2_code)
        )

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

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
        Retrieve a list of Proxy entities with optional filtering and sorting.

        By default, only proxies with a non-null geo_address are returned.
        You can further filter by protocol and country, and limit results.
        If 'only_checked' is True, returns only proxies that have been tested at least once.
        If 'sort_by_unchecked' is True, returns proxies sorted by null 'last_tested' first.

        Args:
            protocol (Protocol | None): Optional protocol to filter proxies by.
            country_alpha2_code (str | None): Optional country code in 3166-1 Alpha-2 format
                to filter proxies by (requires associated geo address).
            only_checked (bool): If True, include only proxies that were tested. Defaults to False.
            offset (int | None): Optional number of records to skip (for pagination).
            limit (int | None): Optional maximum number of proxies to return (for pagination).
            sort_by_unchecked (bool): If True, sort proxies with no 'last_tested' first.
                Cannot be True when 'only_checked' is also True.

        Raises:
            ValueError: If both 'only_checked' and 'sort_by_unchecked' are True.

        Returns:
            list[Proxy]: A list of Proxy entities matching the provided filters.
        """
        if only_checked and sort_by_unchecked:
            raise ValueError("Cannot sort by unchecked if only_checked is True")

        stmt = select(Proxy).where(Proxy.geo_address_id.is_not(None))

        if protocol:
            stmt = stmt.where(Proxy.protocol == protocol)

        if country_alpha2_code:
            stmt = stmt.join(ProxyAddress).join(Country).where(Country.code == country_alpha2_code)

        stmt = stmt.join(ProxyHealth)
        if only_checked:
            stmt = stmt.where(and_(ProxyHealth.last_tested.is_not(None), ProxyHealth.total_conn_attemps > 0))

            # Descending order means latest proxy on the top
            stmt = stmt.order_by(ProxyHealth.last_tested.desc())

        if sort_by_unchecked:
            stmt = stmt.order_by(ProxyHealth.last_tested.asc().nulls_first())

        if offset:
            stmt = stmt.offset(offset)

        if limit:
            stmt = stmt.limit(limit)

        result = await self.session.execute(stmt)

        return list(result.scalars().all())

    async def get_proxies_count(
        self,
        protocol: Protocol | None = None,
        country_alpha2_code: str | None = None,
        *,
        only_checked: bool = False,
    ) -> int:
        """
        Count the number of proxies that match the given filters.

        This method returns the number of proxy entries that have a non-null geo address.
        You can optionally filter by protocol, country, and whether the proxy was checked.

        Args:
            protocol (Protocol | None): Optional protocol to filter proxies by.
            country_alpha2_code (str | None): Optional country code in ISO 3166-1 Alpha-2 format to filter proxies.
            only_checked (bool): If True, count only proxies that have been tested. Defaults to False.

        Returns:
            int: The number of proxies matching the provided filters.
        """
        stmt = select(func.count(distinct(Proxy.id))).select_from(Proxy).where(Proxy.geo_address_id.is_not(None))

        if protocol:
            stmt = stmt.where(Proxy.protocol == protocol)

        if country_alpha2_code:
            stmt = stmt.join(ProxyAddress).join(Country).where(Country.code == country_alpha2_code)

        stmt = stmt.join(ProxyHealth)
        if only_checked:
            stmt = stmt.where(and_(ProxyHealth.last_tested.is_not(None), ProxyHealth.total_conn_attemps > 0))

        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def get_countries(self) -> list[str]:
        """
        Retrieve a list of distinct country codes associated with proxies.

        Returns:
            list[str]: A list of ISO 3166-1 alpha-2 country codes.
        """
        stmt = select(distinct(Country.code)).join(ProxyAddress).order_by(Country.code.asc())

        result = await self.session.execute(stmt)
        return list(result.scalars().all())
