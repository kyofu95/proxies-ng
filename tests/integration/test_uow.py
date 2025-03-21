from ipaddress import ip_address
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.exceptions import DatabaseError, NotFoundError
from app.core.uow import SQLUnitOfWork
from app.models.proxy import Protocol, Proxy
from app.repository.proxy import ProxyRepository
from app.repository.source import SourceRepository


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_uow_basic(db_session_factory: async_sessionmaker[AsyncSession]) -> None:

    uow = SQLUnitOfWork(db_session_factory)
    assert uow.session_factory == db_session_factory
    assert uow.session is None

    async with SQLUnitOfWork(db_session_factory) as uow:
        assert isinstance(uow.session, AsyncSession)
        assert isinstance(uow.proxy_repository, ProxyRepository)
        assert isinstance(uow.source_repository, SourceRepository)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_uow_exceptions(db_session_factory: async_sessionmaker[AsyncSession]) -> None:
    with pytest.raises(NotFoundError):
        async with SQLUnitOfWork(db_session_factory) as uow:
            raise NotFoundError

    with pytest.raises(DatabaseError):
        async with SQLUnitOfWork(db_session_factory) as uow:
            raise SQLAlchemyError

@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_uow_commit_rollback(db_session_factory: async_sessionmaker[AsyncSession]) -> None:
    id_ = uuid4()
    async with SQLUnitOfWork(db_session_factory) as uow:
        proxy = Proxy()
        proxy.id = id_
        proxy.address = ip_address("127.0.1.1")
        proxy.port = 8080
        proxy.protocol = Protocol.SOCKS4

        await uow.proxy_repository.add(proxy)

    async with SQLUnitOfWork(db_session_factory) as uow:
        assert await uow.proxy_repository.get_by_id(id_)

    with pytest.raises(DatabaseError):
        async with SQLUnitOfWork(db_session_factory) as uow:
            proxy = Proxy()
            proxy.id = id_
            proxy.address = ip_address("127.0.1.1")
            proxy.port = 8080
            proxy.protocol = Protocol.SOCKS4

            await uow.proxy_repository.add(proxy)
