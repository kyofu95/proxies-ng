from ipaddress import IPv4Address
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
import pytest_asyncio

from app.core.uow import SQLUnitOfWork
from app.models.proxy import Protocol, Proxy
from app.service.proxy import ProxyService


@pytest_asyncio.fixture(loop_scope="module", scope="module")
async def mock_uow() -> AsyncMock:
    uow = AsyncMock(SQLUnitOfWork)
    uow.__aenter__.return_value = uow
    uow.proxy_repository = AsyncMock()
    uow.source_repository = AsyncMock()
    return uow


@pytest_asyncio.fixture(loop_scope="module", scope="module")
async def service(mock_uow: AsyncMock) -> ProxyService:
    return ProxyService(mock_uow)


@pytest.mark.unit
@pytest.mark.asyncio(loop_scope="module")
async def test_create_proxy(service: ProxyService, mock_uow: AsyncMock) -> None:
    proxy_id = uuid4()
    address = IPv4Address("192.168.1.1")
    port = 8080
    protocol = Protocol.HTTP

    mock_proxy = Proxy()
    mock_proxy.id = proxy_id
    mock_proxy.address = address
    mock_proxy.port = port
    mock_proxy.protocol = protocol

    mock_uow.proxy_repository.add.return_value = mock_proxy
    result = await service.create(address, port, protocol)
    
    mock_uow.proxy_repository.add.assert_called_once()
    assert result == mock_proxy


@pytest.mark.unit
@pytest.mark.asyncio(loop_scope="module")
async def test_get_by_id(service: ProxyService, mock_uow: AsyncMock) -> None:
    proxy_id = uuid4()
    mock_proxy = Proxy()
    mock_proxy.id = proxy_id

    mock_uow.proxy_repository.get_by_id.return_value = mock_proxy
    result = await service.get_by_id(proxy_id)
    
    mock_uow.proxy_repository.get_by_id.assert_called_once_with(proxy_id)
    assert result == mock_proxy


@pytest.mark.unit
@pytest.mark.asyncio(loop_scope="module")
async def test_update_proxy(service: ProxyService, mock_uow: AsyncMock) -> None:
    mock_proxy = Proxy()
    mock_uow.proxy_repository.update.return_value = mock_proxy

    result = await service.update(mock_proxy)
    
    mock_uow.proxy_repository.update.assert_called_once_with(mock_proxy)
    assert result == mock_proxy


@pytest.mark.unit
@pytest.mark.asyncio(loop_scope="module")
async def test_remove_proxy(service: ProxyService, mock_uow: AsyncMock) -> None:
    mock_proxy = Proxy()

    await service.remove(mock_proxy)
    
    mock_uow.proxy_repository.remove.assert_called_once_with(mock_proxy)
