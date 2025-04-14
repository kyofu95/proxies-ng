from collections.abc import AsyncGenerator
from uuid import uuid4

import pycountry
import pytest_asyncio
from sqlalchemy import insert
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from testcontainers.postgres import PostgresContainer

from app.models.base import Base
from app.models.country import Country


@pytest_asyncio.fixture(loop_scope="session", scope="session")
async def db_engine() -> AsyncGenerator[AsyncEngine]:
    with PostgresContainer("postgres:17.4") as postgres_container:
        engine = create_async_engine(
            postgres_container.get_connection_url(driver="asyncpg"),
        )

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async with engine.begin() as conn:
            # insert countries into lookup table
            for country in pycountry.countries:
                stmt = insert(Country).values(
                    {
                        "id": uuid4(),
                        "code": country.alpha_2,
                        "name": country.name,
                    }
                )
                await conn.execute(stmt)
            await conn.commit()

        yield engine

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(loop_scope="session", scope="session")
async def db_session_factory(db_engine: AsyncEngine) -> AsyncGenerator[async_sessionmaker[AsyncSession]]:
    async_session_factory = async_sessionmaker(db_engine, expire_on_commit=False)
    yield async_session_factory
