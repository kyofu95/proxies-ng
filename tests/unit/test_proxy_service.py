from datetime import datetime
from ipaddress import IPv4Address
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
import pytest_asyncio

from app.core.exceptions import CountryCodeError
from app.core.uow import SQLUnitOfWork
from app.models.country import Country
from app.models.proxy import Protocol, Proxy, ProxyAddress, ProxyHealth
from app.service.proxy import InitialHealth, Location, NotFoundError, ProxyService


@pytest_asyncio.fixture(loop_scope="function", scope="function")
async def mock_uow() -> AsyncMock:
    uow = AsyncMock(SQLUnitOfWork)
    uow.__aenter__.return_value = uow
    uow.proxy_repository = AsyncMock()
    uow.source_repository = AsyncMock()
    return uow


@pytest_asyncio.fixture(loop_scope="function", scope="function")
async def service(mock_uow: AsyncMock) -> ProxyService:
    return ProxyService(mock_uow)


@pytest.mark.unit
@pytest.mark.asyncio
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
@pytest.mark.asyncio
async def test_get_by_id(service: ProxyService, mock_uow: AsyncMock) -> None:
    proxy_id = uuid4()
    mock_proxy = Proxy()
    mock_proxy.id = proxy_id

    mock_uow.proxy_repository.get_by_id.return_value = mock_proxy
    result = await service.get_by_id(proxy_id)

    mock_uow.proxy_repository.get_by_id.assert_called_once_with(proxy_id)
    assert result == mock_proxy


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_proxy(service: ProxyService, mock_uow: AsyncMock) -> None:
    mock_proxy = Proxy()
    mock_uow.proxy_repository.update.return_value = mock_proxy

    result = await service.update(mock_proxy)

    mock_uow.proxy_repository.update.assert_called_once_with(mock_proxy)
    assert result == mock_proxy


@pytest.mark.unit
@pytest.mark.asyncio
async def test_remove_proxy(service: ProxyService, mock_uow: AsyncMock) -> None:
    mock_proxy = Proxy()

    await service.remove(mock_proxy)

    mock_uow.proxy_repository.remove.assert_called_once_with(mock_proxy)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_proxies(service: ProxyService, mock_uow: AsyncMock) -> None:
    await service.get_proxies()

    mock_uow.proxy_repository.get_proxies.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_proxies_exception(service: ProxyService, mock_uow: AsyncMock) -> None:
    with pytest.raises(ValueError):
        await service.get_proxies(sort_by_unchecked=True, only_checked=True)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_proxies_country_exception(service: ProxyService, mock_uow: AsyncMock) -> None:
    with pytest.raises(CountryCodeError):
        await service.get_proxies(country_alpha2_code="INVALIDCOUNTRYCODE")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_proxies_count(service: ProxyService, mock_uow: AsyncMock) -> None:
    await service.get_proxies_count()

    mock_uow.proxy_repository.get_proxies_count.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_countries(service: ProxyService, mock_uow: AsyncMock) -> None:
    await service.get_countries()

    mock_uow.proxy_repository.get_countries.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
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
@pytest.mark.asyncio
async def test_update_bulk(service: ProxyService, mock_uow: AsyncMock) -> None:
    proxy1 = Proxy()
    proxy2 = Proxy()

    proxies = [proxy1, proxy2]

    await service.update_bulk(proxies, only_health=True)

    mock_uow.proxy_repository.update_bulk.assert_called_once_with(proxies, only_health=True)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_build(service: ProxyService, mock_uow: AsyncMock) -> None:
    ip_address = IPv4Address("10.0.0.1")
    port = 3128
    protocol = Protocol.HTTPS
    login = "user"
    password = "pass"

    proxy = await service._build(
        address=ip_address,
        port=port,
        protocol=protocol,
        login=login,
        password=password,
    )

    assert proxy.address == ip_address
    assert proxy.port == port
    assert proxy.protocol == protocol
    assert proxy.login == login
    assert proxy.password == password


@pytest.mark.unit
@pytest.mark.asyncio
async def test_build_with_health(service: ProxyService, mock_uow: AsyncMock) -> None:
    ip_address = IPv4Address("10.0.0.1")
    port = 3128
    protocol = Protocol.HTTPS
    login = "user"
    password = "pass"
    latency = 123
    tested_at = datetime.utcnow()

    proxy = await service._build(
        address=ip_address,
        port=port,
        protocol=protocol,
        login=login,
        password=password,
        initial_health=InitialHealth(latency=latency, tested=tested_at),
    )

    assert proxy.address == ip_address
    assert proxy.port == port
    assert proxy.protocol == protocol
    assert proxy.login == login
    assert proxy.password == password

    assert isinstance(proxy.health, ProxyHealth)
    assert proxy.health.total_conn_attempts == 1
    assert proxy.health.latency == latency
    assert proxy.health.last_tested == tested_at
    assert proxy.health.proxy_id == proxy.id


@pytest.mark.unit
@pytest.mark.asyncio
async def test_build_with_health_and_location(service: ProxyService, mock_uow: AsyncMock) -> None:
    location = Location(city="TestCity", region="TestRegion", country_code="US")
    ip_address = IPv4Address("10.0.0.1")
    port = 3128
    protocol = Protocol.HTTPS
    login = "user"
    password = "pass"
    latency = 123
    tested_at = datetime.utcnow()

    fake_geo_address = ProxyAddress()
    fake_geo_address.id = uuid4()
    fake_geo_address.city = location.city
    fake_geo_address.region = location.region

    with patch.object(service, "_resolve_location", new=AsyncMock(return_value=fake_geo_address)) as mock_resolve:
        proxy = await service._build(
            address=ip_address,
            port=port,
            protocol=protocol,
            login=login,
            password=password,
            location=location,
            initial_health=InitialHealth(latency=latency, tested=tested_at),
        )

    mock_resolve.assert_awaited_once_with(location)

    assert proxy.address == ip_address
    assert proxy.port == port
    assert proxy.protocol == protocol
    assert proxy.login == login
    assert proxy.password == password

    assert isinstance(proxy.health, ProxyHealth)
    assert proxy.health.total_conn_attempts == 1
    assert proxy.health.latency == latency
    assert proxy.health.last_tested == tested_at
    assert proxy.health.proxy_id == proxy.id

    assert proxy.geo_address == fake_geo_address
    assert proxy.geo_address.city == fake_geo_address.city


@pytest.mark.unit
@pytest.mark.asyncio
async def test_resolve_location_lookup_success(service: ProxyService, mock_uow: AsyncMock) -> None:
    location_obj = Location(city="X", region="Y", country_code="DE")

    mock_address_country = Country(code="DE", name="Germany")
    mock_address = ProxyAddress(city="X", region="Y", country=mock_address_country)

    mock_uow.proxy_repository.get_geo_address_by_location.return_value = mock_address

    result = await service._resolve_location(location_obj)

    mock_uow.proxy_repository.get_geo_address_by_location.assert_called_once()

    assert result.city == mock_address.city
    assert result.region == mock_address.region
    assert result.country.code == mock_address.country.code


@pytest.mark.unit
@pytest.mark.asyncio
async def test_resolve_location_create_address(service: ProxyService, mock_uow: AsyncMock) -> None:
    location_obj = Location(city="A", region="B", country_code="YY")

    mock_uow.proxy_repository.get_geo_address_by_location.return_value = None

    mock_country = Country(id=uuid4(), code="YY", name="YYYY")
    mock_uow.proxy_repository.get_country_by_code.return_value = mock_country

    mock_uow.proxy_repository.add_geo_address.side_effect = lambda geo: geo

    result = await service._resolve_location(location_obj)

    mock_uow.proxy_repository.get_geo_address_by_location.assert_called_once()
    mock_uow.proxy_repository.get_country_by_code.assert_called_once()
    mock_uow.proxy_repository.add_geo_address.assert_called_once()

    assert result
    assert result.city == location_obj.city
    assert result.region == location_obj.region
    assert result.country.code == mock_country.code


@pytest.mark.unit
@pytest.mark.asyncio
async def test_resolve_location_no_country(service: ProxyService, mock_uow: AsyncMock) -> None:
    location_obj = Location(city="A1", region="B2", country_code="XX")

    mock_uow.proxy_repository.get_geo_address_by_location.return_value = None
    mock_uow.proxy_repository.get_country_by_code.return_value = None

    with pytest.raises(NotFoundError, match=f"Could not find country with code {location_obj.country_code}"):
        await service._resolve_location(location_obj)

    mock_uow.proxy_repository.get_geo_address_by_location.assert_called_once()
    mock_uow.proxy_repository.get_country_by_code.assert_called_once()
