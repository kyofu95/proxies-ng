import random
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.uow import SQLUnitOfWork
from app.models.source import Source, SourceHealth, SourceType


def make_a_source() -> Source:
    name = "".join(map(str, (random.randint(ord("a"), ord("z")) for _ in range(4))))
    ip = ".".join(map(str, (random.randint(0, 255) for _ in range(4))))

    source = Source()
    source.id = uuid4()
    source.name = name
    source.uri = f"http://{ip}:8080/text.txt"
    source.uri_predefined_type = None
    source.type = SourceType.Text

    return source


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_source_repository_add(db_session_factory: async_sessionmaker[AsyncSession]) -> None:

    async with SQLUnitOfWork(db_session_factory) as uow:
        source = make_a_source()
        assert await uow.source_repository.add(source)

    async with SQLUnitOfWork(db_session_factory) as uow:
        stored_source = await uow.source_repository.get_by_id(source.id)
        assert stored_source
        assert stored_source.name == source.name

    async with SQLUnitOfWork(db_session_factory) as uow:
        stored_sources = await uow.source_repository.get_all()
        assert stored_sources
        assert len(stored_sources) == 1

    async with SQLUnitOfWork(db_session_factory) as uow:
        stored_source = await uow.source_repository.get_by_name(source.name)
        assert stored_source
        assert stored_source.name == source.name

@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_source_repository_update(db_session_factory: async_sessionmaker[AsyncSession]) -> None:

    async with SQLUnitOfWork(db_session_factory) as uow:
        source = make_a_source()
        assert await uow.source_repository.add(source)

    async with SQLUnitOfWork(db_session_factory) as uow:
        stored_source = await uow.source_repository.get_by_id(source.id)
        assert stored_source

        health = SourceHealth()
        health.id = uuid4()
        health.total_conn_attemps = 100
        health.failed_conn_attemps = 0

        stored_source.health = health

        stored_source = await uow.source_repository.update(stored_source)
        assert stored_source.health
        assert stored_source.health.total_conn_attemps == health.total_conn_attemps

@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_source_repository_remove(db_session_factory: async_sessionmaker[AsyncSession]) -> None:

    async with SQLUnitOfWork(db_session_factory) as uow:
        source = make_a_source()
        assert await uow.source_repository.add(source)

    async with SQLUnitOfWork(db_session_factory) as uow:
        stored_source = await uow.source_repository.get_by_id(source.id)
        assert stored_source
        await uow.source_repository.remove(stored_source)

    async with SQLUnitOfWork(db_session_factory) as uow:
        stored_source = await uow.source_repository.get_by_id(source.id)
        assert stored_source is None
