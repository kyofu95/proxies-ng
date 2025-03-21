from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from testcontainers.postgres import PostgresContainer

from app.models.base import Base


@pytest_asyncio.fixture(loop_scope="session", scope="session")
async def db_engine() -> AsyncGenerator[AsyncEngine]:

    with PostgresContainer("postgres:17.4") as postgres_container:

        engine = create_async_engine(
            postgres_container.get_connection_url(driver="asyncpg"),
        )

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        yield engine

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(loop_scope="session", scope="session")
async def db_session_factory(db_engine: AsyncEngine) -> AsyncGenerator[async_sessionmaker[AsyncSession]]:
    async_session_factory = async_sessionmaker(db_engine, expire_on_commit=False)
    yield async_session_factory

@pytest_asyncio.fixture(loop_scope="session", scope="function")
async def db_session(
    db_session_factory: async_sessionmaker[AsyncSession],
    monkeypatch: pytest.MonkeyPatch,
) -> AsyncGenerator[AsyncSession]:

    async with db_session_factory() as session:
        await session.begin()

        yield session

        await session.rollback()
