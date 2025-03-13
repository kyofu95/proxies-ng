from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.source import Source

from .base import BaseRepository


class SourceRepository(BaseRepository[Source]):
    """
    Repository for handling database operations related to the Source model.

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

    async def add(self, entity: Source) -> Source:
        """
        Add a new Source entity to the database.

        Args:
            entity (Source): The Source entity to add.

        Returns:
            Source: The added Source entity.
        """
        self.session.add(entity)
        await self.session.commit()
        return entity

    async def get_by_id(self, id_: UUID) -> Source | None:
        """
        Retrieve a Source entity by its ID.

        Args:
            id_ (UUID): The ID of the Source entity.

        Returns:
            Source | None: The Source entity if found, otherwise None.
        """
        return await self.session.get(Source, id_)

    async def update(self, entity: Source) -> Source:
        """
        Update an existing Source entity in the database.

        Args:
            entity (Source): The Source entity to update.

        Raises:
            NotFoundError: If the entity does not exist in the database.

        Returns:
            Source: The updated Source entity.
        """
        stored_entity = await self.session.get(Source, entity.id)
        if not stored_entity:
            raise NotFoundError(
                "Entity has not been stored in database, but were marked for update.",
            )

        await self.session.flush([entity])
        await self.session.commit()
        await self.session.refresh(entity)

        return entity

    async def remove(self, entity: Source) -> None:
        """
        Remove a Source entity from the database.

        Args:
            entity (Source): The Source entity to remove.
        """
        await self.session.delete(entity)
        await self.session.commit()
