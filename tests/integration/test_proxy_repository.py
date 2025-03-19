from ipaddress import ip_address
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.proxy import Protocol, Proxy, ProxyAddress, ProxyHealth
from app.repository.proxy import ProxyRepository


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_anime_repository_basic(db_session: AsyncSession) -> None:

    proxy_repo = ProxyRepository(db_session)

    health = ProxyHealth()
    health.id = uuid4()
    health.total_conn_attemps = 4
    health.failed_conn_attemps = 0

    proxy = Proxy()
    proxy.id = uuid4()
    proxy.address = ip_address("127.0.0.1")
    proxy.port = 8080
    proxy.protocol = Protocol.SOCKS4
    proxy.geo_address = None
    
    proxy.health = health

    await proxy_repo.add(proxy)

    stored_proxy = await proxy_repo.get_by_id(proxy.id)
    assert stored_proxy
    assert stored_proxy.id == proxy.id

    stored_proxy.health.total_conn_attemps = 5

    await proxy_repo.update(stored_proxy)
    stored_proxy = await proxy_repo.get_by_id(proxy.id)
    assert stored_proxy
    assert stored_proxy.id == proxy.id
    assert stored_proxy.health.total_conn_attemps == 5

    await proxy_repo.remove(stored_proxy)

    stored_proxy = await proxy_repo.get_by_id(proxy.id)
    assert stored_proxy is None

@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_anime_repository_geo_address(db_session: AsyncSession) -> None:

    proxy_repo = ProxyRepository(db_session)

    geo_address = ProxyAddress()
    geo_address.id = uuid4()
    geo_address.city = "Chicago"
    geo_address.country = "USA"
    geo_address.region = "Illinois"

    stored_geo_address = await proxy_repo.add_geo_address(geo_address)
    assert stored_geo_address
    assert stored_geo_address.country == geo_address.country

    stored_geo_address = await proxy_repo.get_geo_address_by_id(geo_address.id)
    assert stored_geo_address
    assert stored_geo_address.country == geo_address.country

    stored_geo_address = await proxy_repo.get_geo_address_by_location("USA", "Illinois", "Chicago")
    assert stored_geo_address
    assert stored_geo_address.country == geo_address.country
    assert stored_geo_address.region == geo_address.region
    assert stored_geo_address.city == geo_address.city

    health = ProxyHealth()
    health.id = uuid4()
    health.total_conn_attemps = 4
    health.failed_conn_attemps = 0

    proxy = Proxy()
    proxy.id = uuid4()
    proxy.address = ip_address("127.0.0.1")
    proxy.port = 8080
    proxy.protocol = Protocol.SOCKS4
    proxy.geo_address = None
    
    proxy.health = health

    stored_proxy = await proxy_repo.add(proxy)
    assert stored_proxy.geo_address is None

    stored_proxy.geo_address = stored_geo_address
    stored_proxy = await proxy_repo.update(stored_proxy)
    assert stored_proxy.geo_address
    assert stored_proxy.geo_address.country == geo_address.country
    assert stored_proxy.geo_address.region == geo_address.region
    assert stored_proxy.geo_address.city == geo_address.city

    await proxy_repo.remove(stored_proxy)

    stored_geo_address = await proxy_repo.get_geo_address_by_id(geo_address.id)
    assert stored_geo_address
    assert stored_geo_address.country == geo_address.country
