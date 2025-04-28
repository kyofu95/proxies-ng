from ipaddress import IPv4Address
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
import pytest_asyncio

from app.core.uow import SQLUnitOfWork
from app.models.proxy import Protocol, Proxy
from app.service.proxy import Location, ProxyService


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
    location = Location(city="A", region="B", country_code="US")

    mock_proxy = Proxy()
    mock_proxy.id = proxy_id
    mock_proxy.address = address
    mock_proxy.port = port
    mock_proxy.protocol = protocol
    mock_proxy.address = location

    mock_uow.proxy_repository.add.return_value = mock_proxy
    result = await service.create(address, port, protocol, location=location)

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


@pytest.mark.unit
@pytest.mark.asyncio(loop_scope="module")
async def test_get_proxies(service: ProxyService, mock_uow: AsyncMock) -> None:
    await service.get_proxies()

    mock_uow.proxy_repository.get_proxies.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio(loop_scope="module")
async def test_get_proxies_exception(service: ProxyService, mock_uow: AsyncMock) -> None:
    with pytest.raises(ValueError):
        await service.get_proxies(sort_by_unchecked=True, only_checked=True)


@pytest.mark.unit
@pytest.mark.asyncio(loop_scope="module")
async def test_proxies_count(service: ProxyService, mock_uow: AsyncMock) -> None:
    await service.get_proxies_count()

    mock_uow.proxy_repository.get_proxies_count.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio(loop_scope="module")
async def test_get_countries(service: ProxyService, mock_uow: AsyncMock) -> None:
    await service.get_countries()

    mock_uow.proxy_repository.get_countries.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio(loop_scope="module")
async def test_create_bulk(service: ProxyService, mock_uow: AsyncMock) -> None:
    proxy_data_1 = {
        "address": IPv4Address("192.168.1.1"),
        "port": 8080,
        "protocol": Protocol.HTTP,
        "location": Location(city="City1", region="Region1", country_code="FR"),
    }
    proxy_data_2 = {
        "address": IPv4Address("192.168.1.2"),
        "port": 9090,
        "protocol": Protocol.HTTPS,
        "location": Location(city="City2", region="Region2", country_code="NL"),
    }

    proxies_data = [proxy_data_1, proxy_data_2]

    mock_proxy_1 = Proxy()
    mock_proxy_1.address = proxy_data_1["address"]
    mock_proxy_1.port = proxy_data_1["port"]
    mock_proxy_1.protocol = proxy_data_1["protocol"]
    mock_proxy_1.geo_address = None

    mock_proxy_2 = Proxy()
    mock_proxy_2.address = proxy_data_2["address"]
    mock_proxy_2.port = proxy_data_2["port"]
    mock_proxy_2.protocol = proxy_data_2["protocol"]
    mock_proxy_2.geo_address = None

    mock_uow.proxy_repository.add_bulk.return_value = None

    await service.create_bulk(proxies_data)

    mock_uow.proxy_repository.add_bulk.assert_called_once()

    args, kwargs = mock_uow.proxy_repository.add_bulk.call_args

    proxies = args[0]
    assert len(proxies) == 2
    assert proxies[0].address == mock_proxy_1.address
    assert proxies[0].port == mock_proxy_1.port
    assert proxies[0].protocol == mock_proxy_1.protocol
    assert proxies[1].address == mock_proxy_2.address
    assert proxies[1].port == mock_proxy_2.port
    assert proxies[1].protocol == mock_proxy_2.protocol


@pytest.mark.unit
@pytest.mark.asyncio(loop_scope="module")
async def test_update_bulk(service: ProxyService, mock_uow: AsyncMock) -> None:
    proxy1 = Proxy()
    proxy2 = Proxy()

    proxies = [proxy1, proxy2]

    await service.update_bulk(proxies, only_health=True)

    mock_uow.proxy_repository.update_bulk.assert_called_once_with(proxies, only_health=True)
