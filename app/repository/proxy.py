from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.proxy import Proxy

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
