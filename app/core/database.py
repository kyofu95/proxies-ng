from sqlalchemy import URL
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from .config import database_settings


def create_session_factory() -> async_sessionmaker[AsyncSession]:
    """
    Create and returns a session factory for working with an asynchronous database.

    The purpose of this function is to ensure proper session handling in asynchronous
    Celery tasks or other asynchronous contexts, where each event loop must have its
    own session to avoid conflicts between tasks.

    Features:
        - The function creates a new database connection and session factory
        for each call, ensuring that each asynchronous task works with its
        own session instance.
        - This factory is primarily used in Celery asynchronous tasks to create
        sessions within their event loops.

    Returns:
        async_sessionmaker: A session factory for creating instances of AsyncSession.

    Notes:
        - It's important to use this factory within asynchronous tasks and
        event loops to avoid errors related to attempting to use sessions
        tied to different loops.
    """
    connection_url = URL.create(
        drivername=database_settings.driver,
        username=database_settings.user,
        password=database_settings.password,
        host=database_settings.host,
        port=database_settings.port,
        database=database_settings.name,
    )
    engine = create_async_engine(connection_url, pool_size=10, max_overflow=2)
    return async_sessionmaker(engine, expire_on_commit=False)


async_session_factory = create_session_factory()
