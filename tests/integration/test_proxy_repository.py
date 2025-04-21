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
    proxy = Proxy()
    proxy.id = uuid4()
    proxy.address = random_ipv4()
    proxy.port = 8080
    proxy.protocol = Protocol.SOCKS4
    proxy.geo_address = None

    proxy.health = ProxyHealth()
    proxy.health.id = uuid4()
    proxy.health.total_conn_attemps = 4
    proxy.health.failed_conn_attemps = 0
    proxy.health.latency = 0
    proxy.health.last_tested = None
    proxy.health.proxy_id = proxy.id

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
        geo_address.region = "Illinois"
        geo_address.country = await uow.proxy_repository.get_country_by_code("US")
        assert geo_address.country
        geo_address.country_id = geo_address.country.id

        stored_geo_address = await uow.proxy_repository.add_geo_address(geo_address)
        assert stored_geo_address
        assert stored_geo_address.country == geo_address.country

    async with SQLUnitOfWork(db_session_factory) as uow:
        stored_geo_address_a = await uow.proxy_repository.get_geo_address_by_id(geo_address.id)
        assert stored_geo_address_a
        assert stored_geo_address_a.country.name == geo_address.country.name

    async with SQLUnitOfWork(db_session_factory) as uow:
        stored_geo_address_b = await uow.proxy_repository.get_geo_address_by_location("US", "Illinois", "Chicago")
        assert stored_geo_address_b
        assert stored_geo_address_b.country.name == geo_address.country.name
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

    async with SQLUnitOfWork(db_session_factory) as uow:
        geo_address = ProxyAddress()
        geo_address.id = uuid4()
        geo_address.city = "Detroit"
        geo_address.country = await uow.proxy_repository.get_country_by_code("US")
        geo_address.region = "Michigan"
        assert geo_address.country
        geo_address.country_id = geo_address.country.id

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
        assert stored_proxy.geo_address.country.name == geo_address.country.name
        assert stored_proxy.geo_address.region == geo_address.region
        assert stored_proxy.geo_address.city == geo_address.city

    async with SQLUnitOfWork(db_session_factory) as uow:
        stored_proxy = await uow.proxy_repository.get_by_id(proxy.id)
        assert stored_proxy
        await uow.proxy_repository.remove(stored_proxy)

    async with SQLUnitOfWork(db_session_factory) as uow:
        stored_geo_address = await uow.proxy_repository.get_geo_address_by_id(geo_address.id)
        assert stored_geo_address
        assert stored_geo_address.country.name == geo_address.country.name


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_proxy_repository_get_geo_address_by_location(
    db_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with SQLUnitOfWork(db_session_factory) as uow:
        stored_geo_address = await uow.proxy_repository.get_geo_address_by_location("NL", "A", "B")
        assert not stored_geo_address


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_proxy_repository_get_proxies(db_session_factory: async_sessionmaker[AsyncSession]) -> None:
    async with SQLUnitOfWork(db_session_factory) as uow:
        proxy = make_proxy()
        proxy.protocol = Protocol.HTTPS
        geo_address = ProxyAddress()
        geo_address.id = uuid4()
        geo_address.city = "Amsterdam"
        geo_address.country = await uow.proxy_repository.get_country_by_code("NL")
        geo_address.region = "North Holland"
        assert geo_address.country
        geo_address.country_code = geo_address.country.id
        proxy.geo_address = geo_address

        await uow.proxy_repository.add(proxy)

        proxy = make_proxy()
        proxy.protocol = Protocol.HTTPS
        geo_address = ProxyAddress()
        geo_address.id = uuid4()
        geo_address.city = "Utrecht"
        geo_address.country = await uow.proxy_repository.get_country_by_code("NL")
        geo_address.region = "Utrecht"
        assert geo_address.country
        geo_address.country_code = geo_address.country.id
        proxy.geo_address = geo_address

        await uow.proxy_repository.add(proxy)

        proxy = make_proxy()
        proxy.protocol = Protocol.HTTPS
        geo_address = ProxyAddress()
        geo_address.id = uuid4()
        geo_address.city = "Lyon"
        geo_address.country = await uow.proxy_repository.get_country_by_code("FR")
        geo_address.region = "Auvergne-Rhone-Alpes"
        assert geo_address.country
        geo_address.country_code = geo_address.country.id
        proxy.geo_address = geo_address

        await uow.proxy_repository.add(proxy)

        proxy = make_proxy()
        proxy.protocol = Protocol.HTTP

        await uow.proxy_repository.add(proxy)

    async with SQLUnitOfWork(db_session_factory) as uow:
        with pytest.raises(ValueError):
            proxies = await uow.proxy_repository.get_proxies(only_checked=True, sort_by_unchecked=True)

        proxies = await uow.proxy_repository.get_proxies()
        assert len(proxies) >= 3

        proxies = await uow.proxy_repository.get_proxies(protocol=None, country_alpha2_code="NL")
        assert len(proxies) == 2

        proxies = await uow.proxy_repository.get_proxies(protocol=None, country_alpha2_code="Germany")
        assert len(proxies) == 0

        proxies = await uow.proxy_repository.get_proxies(protocol=Protocol.HTTPS, country_alpha2_code=None)
        assert len(proxies) == 3

        proxies = await uow.proxy_repository.get_proxies(protocol=Protocol.SOCKS5, country_alpha2_code=None)
        assert len(proxies) == 0

        proxies = await uow.proxy_repository.get_proxies(protocol=Protocol.HTTP, country_alpha2_code=None)
        assert len(proxies) == 0

        proxies = await uow.proxy_repository.get_proxies(only_checked=True)
        assert len(proxies) == 0

        proxies = await uow.proxy_repository.get_proxies(limit=1)
        assert len(proxies) == 1

        proxies = await uow.proxy_repository.get_proxies(limit=2)
        assert len(proxies) == 2

        proxies = await uow.proxy_repository.get_proxies(sort_by_unchecked=True)
        assert len(proxies) == 3


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_proxy_repository_add_bulk(db_session_factory: async_sessionmaker[AsyncSession]) -> None:
    async with SQLUnitOfWork(db_session_factory) as uow:
        proxies = [make_proxy() for _ in range(3)]
        await uow.proxy_repository.add_bulk(proxies)


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_proxy_repository_get_country_by_code(db_session_factory: async_sessionmaker[AsyncSession]) -> None:
    async with SQLUnitOfWork(db_session_factory) as uow:
        country = await uow.proxy_repository.get_country_by_code("US")
        assert country.name == "United States"

        country = await uow.proxy_repository.get_country_by_code("XX")
        assert not country


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_proxy_repository_proxies_count(db_session_factory: async_sessionmaker[AsyncSession]) -> None:
    async with SQLUnitOfWork(db_session_factory) as uow:
        proxy = make_proxy()
        proxy.protocol = Protocol.HTTPS
        geo_address = ProxyAddress()
        geo_address.id = uuid4()
        geo_address.city = "Dallas"
        geo_address.country = await uow.proxy_repository.get_country_by_code("US")
        geo_address.region = "Texas"
        assert geo_address.country
        geo_address.country_code = geo_address.country.id
        proxy.geo_address = geo_address

        await uow.proxy_repository.add(proxy)

    async with SQLUnitOfWork(db_session_factory) as uow:
        count = await uow.proxy_repository.get_proxies_count()
        assert count


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_proxy_repository_get_countries(db_session_factory: async_sessionmaker[AsyncSession]) -> None:
    async with SQLUnitOfWork(db_session_factory) as uow:
        de = await uow.proxy_repository.get_country_by_code("DE")
        us = await uow.proxy_repository.get_country_by_code("US")
        fr = await uow.proxy_repository.get_country_by_code("FR")

        address1 = ProxyAddress(id=uuid4(), country_id=de.id, region="Bavaria", city="Munich")
        address2 = ProxyAddress(id=uuid4(), country_id=us.id, region="California", city="LA")
        address3 = ProxyAddress(id=uuid4(), country_id=us.id, region="New York", city="NYC")
        address4 = ProxyAddress(id=uuid4(), country_id=fr.id, region="Île-de-France", city="Paris")

        uow.session.add_all([address1, address2, address3, address4])

    async with SQLUnitOfWork(db_session_factory) as uow:
        countries = await uow.proxy_repository.get_countries()
        assert countries
        assert "DE" in countries
        assert "US" in countries
        assert "FR" in countries
