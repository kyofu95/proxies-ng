from uuid import UUID

from sqlalchemy import and_, insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AlreadyExistsError, NotFoundError
from app.models.proxy import Proxy, ProxyAddress

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
        await self.session.commit()
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
        await self.session.commit()
        await self.session.refresh(entity)

        return entity

    async def remove(self, entity: Proxy) -> None:
        """
        Remove a Proxy entity from the database.

        Args:
            entity (Proxy): The Proxy entity to remove.
        """
        await self.session.delete(entity)
        await self.session.commit()

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
            geo_address.country, geo_address.region, geo_address.city,
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
        address = result.scalar_one()
        await self.session.commit()
        return address

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
