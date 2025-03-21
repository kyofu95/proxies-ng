from types import TracebackType
from typing import Self

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.repository.proxy import ProxyRepository
from app.repository.source import SourceRepository

from .exceptions import BaseError, DatabaseError


class SQLUnitOfWork:
    """
    Unit of Work pattern implementation for managing database transactions.

    This class ensures that database operations are executed within a transaction,
    committing changes if successful and rolling back in case of errors.
    """

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        """
        Initialize the Unit of Work with a session factory.

        Args:
            session_factory (async_sessionmaker[AsyncSession]): The session factory to create new sessions.
        """
        self.session_factory = session_factory
        self.session: AsyncSession | None = None

    async def __aenter__(self) -> Self:
        """
        Enters the async context, creating a new database session and initializing repositories.

        Returns:
            Self: The current instance of SQLUnitOfWork.
        """
        self.session = self.session_factory()
        self.proxy_repository = ProxyRepository(self.session)
        self.source_repository = SourceRepository(self.session)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool | None:
        """
        Exit the async context, handling commit or rollback depending on the exception state.

        Args:
            exc_type (type[BaseException] | None): The exception type if raised.
            exc_value (BaseException | None): The exception instance if raised.
            exc_tb (TracebackType | None): The traceback if an exception occurred.

        Returns:
            bool | None: False if a logical exception occurs, otherwise None.

        Raises:
            DatabaseError: If an SQLAlchemy error occurs during execution.
        """
        if exc_type:
            await self._rollback()
        else:
            try:
                await self._commit()
            except SQLAlchemyError as exc:
                exc_type = type(exc)
                exc_value = exc

                await self._rollback()

        if self.session:
            await self.session.close()

        # do not omit logic exceptions
        if isinstance(exc_value, BaseError):
            return False

        # but process sqlalchemy exceptions
        if isinstance(exc_value, SQLAlchemyError):
            raise DatabaseError from exc_value

        return False

    async def _commit(self) -> None:
        """Commit the current transaction."""
        if self.session:
            await self.session.commit()

    async def _rollback(self) -> None:
        """Roll back the current transaction."""
        if self.session:
            await self.session.rollback()
