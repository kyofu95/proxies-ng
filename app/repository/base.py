from abc import ABC, abstractmethod
from typing import Generic, TypeVar
from uuid import UUID

T = TypeVar("T")


class BaseRepository(ABC, Generic[T]):
    """Base repository class."""

    @abstractmethod
    async def add(self, entity: T) -> T:
        """Store entity. Abstract method."""
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, id_: UUID) -> T | None:
        """Get entity by id. Abstract method."""
        raise NotImplementedError

    @abstractmethod
    async def update(self, entity: T) -> T:
        """Update entity. Abstract method."""
        raise NotImplementedError

    @abstractmethod
    async def remove(self, entity: T) -> None:
        """Remove entity. Abstract method."""
        raise NotImplementedError
