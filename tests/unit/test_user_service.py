from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
import pytest_asyncio

from app.core.exceptions import AlreadyExistsError
from app.core.uow import SQLUnitOfWork
from app.models.user import User
from app.service.user import UserService


@pytest_asyncio.fixture(loop_scope="function", scope="function")
async def mock_uow() -> AsyncMock:
    uow = AsyncMock(SQLUnitOfWork)
    uow.__aenter__.return_value = uow
    uow.user_repository = AsyncMock()
    return uow


@pytest_asyncio.fixture(loop_scope="function", scope="function")
async def service(mock_uow: AsyncMock) -> UserService:
    return UserService(mock_uow)


@pytest.mark.unit
@pytest.mark.asyncio
@patch("app.service.user.Hasher.hash", return_value="hashed_password")
async def test_create_user(mock_hash, service: UserService, mock_uow: AsyncMock):
    login = "test_user"
    password = "password123"
    user_id = uuid4()
    created_user = User(id=user_id, login=login, password="hashed_password")

    mock_uow.user_repository.get_by_login.return_value = None
    mock_uow.user_repository.add.return_value = created_user

    user = await service.create(login, password)

    mock_uow.user_repository.add.assert_called_once()
    assert user == created_user
    assert user.login == login
    assert user.password == "hashed_password"
    mock_hash.assert_called_once_with(password)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_user_already_exists(service: UserService, mock_uow: AsyncMock):
    login = "existing_user"
    password = "some_pass"
    mock_uow.user_repository.get_by_login.return_value = User(id=uuid4(), login=login, password="hashed")

    with pytest.raises(AlreadyExistsError):
        await service.create(login, password)

    mock_uow.user_repository.get_by_login.assert_called_once_with(login)
    mock_uow.user_repository.add.assert_not_called()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_by_id(service: UserService, mock_uow: AsyncMock):
    user_id = uuid4()
    user = User(id=user_id, login="john", password="pass")
    mock_uow.user_repository.get_by_id.return_value = user

    result = await service.get_by_id(user_id)

    mock_uow.user_repository.get_by_id.assert_called_once_with(user_id)
    assert result == user


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_by_login(service: UserService, mock_uow: AsyncMock):
    login = "john"
    user = User(id=uuid4(), login=login, password="pass")
    mock_uow.user_repository.get_by_login.return_value = user

    result = await service.get_by_login(login)

    mock_uow.user_repository.get_by_login.assert_called_once_with(login)
    assert result == user


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_user(service: UserService, mock_uow: AsyncMock):
    user = User(id=uuid4(), login="john", password="pass")
    mock_uow.user_repository.update.return_value = user

    result = await service.update(user)

    mock_uow.user_repository.update.assert_called_once_with(user)
    assert result == user


@pytest.mark.unit
@pytest.mark.asyncio
async def test_remove_user(service: UserService, mock_uow: AsyncMock):
    user = User(id=uuid4(), login="john", password="pass")

    await service.remove(user)

    mock_uow.user_repository.remove.assert_called_once_with(user)
