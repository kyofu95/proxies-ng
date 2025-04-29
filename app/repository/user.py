from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User

from .base import BaseRepository


class UserRepository(BaseRepository[User]):
    """
    Repository for handling database operations related to the User model.

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

    async def add(self, user: User) -> User:
        """
        Add a new User entity to the database.

        Args:
            user (User): The User entity to add.

        Returns:
            User: The added User entity.
        """
        self.session.add(user)
        return user

    async def get_by_id(self, id_: UUID) -> User | None:
        """
        Retrieve a User entity by its ID.

        Args:
            id_ (UUID): The ID of the User entity.

        Returns:
            User | None: The User entity if found, otherwise None.
        """
        stmt = select(User).where(User.id == id_)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_login(self, login: str) -> User | None:
        """
        Retrieve a User entity by its login.

        Args:
            login (str): The login of the User entity.

        Returns:
            User | None: The User entity if found, otherwise None.
        """
        stmt = select(User).where(User.login == login)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update(self, user: User) -> User:
        """
        Update an existing User entity in the database.

        Args:
            user (User): The User entity to update.

        Returns:
            User: The updated User entity.
        """
        stmt = update(User).where(User.id == user.id).values(user.to_dict()).returning(User)
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def remove(self, user: User) -> None:
        """
        Remove a User entity from the database.

        Args:
            user (User): The User entity to remove.
        """
        await self.session.delete(user)
