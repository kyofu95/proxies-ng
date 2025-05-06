from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.source import Source, SourceHealth

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

    async def get_by_name(self, name: str) -> Source | None:
        """
        Retrieve a Source entity by its name.

        Args:
            name (str): The name of the Source entity.

        Returns:
            Source | None: The Source entity if found, otherwise None.
        """
        stmt = select(Source).where(Source.name == name)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

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

        if entity.health:
            stmt = update(SourceHealth).where(SourceHealth.id == entity.health.id).values(entity.health.to_dict())
            await self.session.execute(stmt)

        stmt = update(Source).where(Source.id == entity.id).values(entity.to_dict()).returning(Source)
        result = await self.session.execute(stmt)

        return result.scalar_one()

    async def remove(self, entity: Source) -> None:
        """
        Remove a Source entity from the database.

        Args:
            entity (Source): The Source entity to remove.
        """
        await self.session.delete(entity)

    async def get_sources(self) -> list[Source]:
        """
        Retrieve all Source entities from the database.

        This is functionally identical to `get_all()` but may be used
        in contexts where naming clarity or consistency is preferred.

        Returns:
            list[Source]: A list of all Source entities.
        """
        stmt = select(Source)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
