import random
from ipaddress import IPv4Address, IPv6Address, ip_address
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.uow import SQLUnitOfWork
from app.models.proxy import Protocol, Proxy, ProxyAddress, ProxyHealth


def random_ipv4() -> IPv4Address | IPv6Address:
    ip = ".".join(map(str, (random.randint(0, 255) for _ in range(4))))
    return ip_address(ip)

def make_proxy() -> Proxy:
    health = ProxyHealth()
    health.id = uuid4()
    health.total_conn_attemps = 4
    health.failed_conn_attemps = 0

    proxy = Proxy()
    proxy.id = uuid4()
    proxy.address = random_ipv4()
    proxy.port = 8080
    proxy.protocol = Protocol.SOCKS4
    proxy.geo_address = None

    proxy.health = health

    return proxy

@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_proxy_repository_add(db_session_factory: async_sessionmaker[AsyncSession]) -> None:

    async with SQLUnitOfWork(db_session_factory) as uow:
        proxy = make_proxy()
        await uow.proxy_repository.add(proxy)

    async with SQLUnitOfWork(db_session_factory) as uow:
        stored_proxy = await uow.proxy_repository.get_by_id(proxy.id)
        assert stored_proxy
        assert stored_proxy.id == proxy.id

@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_proxy_repository_update(db_session_factory: async_sessionmaker[AsyncSession]) -> None:

    async with SQLUnitOfWork(db_session_factory) as uow:
        proxy = make_proxy()
        await uow.proxy_repository.add(proxy)

    async with SQLUnitOfWork(db_session_factory) as uow:
        stored_proxy = await uow.proxy_repository.get_by_id(proxy.id)
        assert stored_proxy

        stored_proxy.health.total_conn_attemps = 5

        await uow.proxy_repository.update(stored_proxy)

    async with SQLUnitOfWork(db_session_factory) as uow:
        stored_proxy = await uow.proxy_repository.get_by_id(proxy.id)
        assert stored_proxy
        assert stored_proxy.id == proxy.id
        assert stored_proxy.health.total_conn_attemps == 5

@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_proxy_repository_remove(db_session_factory: async_sessionmaker[AsyncSession]) -> None:

    async with SQLUnitOfWork(db_session_factory) as uow:
        proxy = make_proxy()
        await uow.proxy_repository.add(proxy)

    async with SQLUnitOfWork(db_session_factory) as uow:
        stored_proxy = await uow.proxy_repository.get_by_id(proxy.id)
        assert stored_proxy
        await uow.proxy_repository.remove(stored_proxy)

    async with SQLUnitOfWork(db_session_factory) as uow:
        stored_proxy = await uow.proxy_repository.get_by_id(proxy.id)
        assert stored_proxy is None

@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_proxy_repository_geo_address_add(db_session_factory: async_sessionmaker[AsyncSession]) -> None:

    async with SQLUnitOfWork(db_session_factory) as uow:

        geo_address = ProxyAddress()
        geo_address.id = uuid4()
        geo_address.city = "Chicago"
        geo_address.country = "USA"
        geo_address.region = "Illinois"

        stored_geo_address = await uow.proxy_repository.add_geo_address(geo_address)
        assert stored_geo_address
        assert stored_geo_address.country == geo_address.country

    async with SQLUnitOfWork(db_session_factory) as uow:
        stored_geo_address_a = await uow.proxy_repository.get_geo_address_by_id(geo_address.id)
        assert stored_geo_address_a
        assert stored_geo_address_a.country == geo_address.country

    async with SQLUnitOfWork(db_session_factory) as uow:
        stored_geo_address_b = await uow.proxy_repository.get_geo_address_by_location("USA", "Illinois", "Chicago")
        assert stored_geo_address_b
        assert stored_geo_address_b.country == geo_address.country
        assert stored_geo_address_b.region == geo_address.region
        assert stored_geo_address_b.city == geo_address.city

@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_proxy_repository_geo_address_proxy(db_session_factory: async_sessionmaker[AsyncSession]) -> None:

    health = ProxyHealth()
    health.id = uuid4()
    health.total_conn_attemps = 4
    health.failed_conn_attemps = 0

    proxy = Proxy()
    proxy.id = uuid4()
    proxy.address = ip_address("127.0.2.1")
    proxy.port = 8080
    proxy.protocol = Protocol.SOCKS4
    proxy.geo_address = None

    proxy.health = health

    geo_address = ProxyAddress()
    geo_address.id = uuid4()
    geo_address.city = "Detroit"
    geo_address.country = "USA"
    geo_address.region = "Michigan"

    async with SQLUnitOfWork(db_session_factory) as uow:
        assert await uow.proxy_repository.add(proxy)
        assert await uow.proxy_repository.add_geo_address(geo_address)

    async with SQLUnitOfWork(db_session_factory) as uow:
        stored_proxy = await uow.proxy_repository.get_by_id(proxy.id)
        stored_geo_address = await uow.proxy_repository.get_geo_address_by_id(geo_address.id)
        assert stored_proxy
        assert stored_geo_address

        stored_proxy.geo_address = stored_geo_address
        stored_proxy = await uow.proxy_repository.update(stored_proxy)
        assert stored_proxy.geo_address
        assert stored_proxy.geo_address.country == geo_address.country
        assert stored_proxy.geo_address.region == geo_address.region
        assert stored_proxy.geo_address.city == geo_address.city

    async with SQLUnitOfWork(db_session_factory) as uow:
        stored_proxy = await uow.proxy_repository.get_by_id(proxy.id)
        assert stored_proxy
        await uow.proxy_repository.remove(stored_proxy)

    async with SQLUnitOfWork(db_session_factory) as uow:
        stored_geo_address = await uow.proxy_repository.get_geo_address_by_id(geo_address.id)
        assert stored_geo_address
        assert stored_geo_address.country == geo_address.country
