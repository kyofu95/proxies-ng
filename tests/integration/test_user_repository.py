from uuid import UUID, uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.uow import SQLUnitOfWork
from app.models.user import User
from app.repository.user import UserRepository


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_user_repository_add(db_session_factory: async_sessionmaker[AsyncSession]) -> None:
    async with SQLUnitOfWork(db_session_factory) as uow:
        id_ = uuid4()
        login = "abc"
        user = User(id=id_, login=login, password="123")  # noqa: S106
        user = await uow.user_repository.add(user)
        assert user

        created_user = await uow.user_repository.get_by_id(id_)
        assert created_user
        created_user = await uow.user_repository.get_by_login(login)
        assert created_user


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_user_repository_get_by(db_session_factory: async_sessionmaker[AsyncSession]) -> None:
    async with SQLUnitOfWork(db_session_factory) as uow:
        created_user = await uow.user_repository.get_by_id(uuid4())
        assert not created_user
        created_user = await uow.user_repository.get_by_login("invalid_login")
        assert not created_user


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_user_repository_update(db_session_factory: async_sessionmaker[AsyncSession]) -> None:
    async with SQLUnitOfWork(db_session_factory) as uow:
        id_ = uuid4()
        login = "def"
        user = User(id=id_, login=login, password="really_bad_password")  # noqa: S106
        user = await uow.user_repository.add(user)
        assert user

        user = await uow.user_repository.get_by_id(id_)
        assert user

        user.password = "really_good_password"  # noqa: S105
        await uow.user_repository.update(user)

        user = await uow.user_repository.get_by_login(login)
        assert user.password == "really_good_password"


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_user_repository_remove(db_session_factory: async_sessionmaker[AsyncSession]) -> None:
    async with SQLUnitOfWork(db_session_factory) as uow:
        id_ = uuid4()
        login = "ghi"
        user = User(id=id_, login=login, password="456")  # noqa: S106
        user = await uow.user_repository.add(user)
        assert user

        user = await uow.user_repository.get_by_id(id_)
        assert user

        await uow.user_repository.remove(user)

        user = await uow.user_repository.get_by_id(id_)
        assert not user
