import datetime
from unittest.mock import AsyncMock, patch

import pytest

from app.models.proxy import Protocol, Proxy, ProxyHealth
from app.tasks.check_proxies import check_single_proxy


@pytest.fixture
def proxy():
    return Proxy(
        address="1.2.3.4",
        port=8080,
        protocol=Protocol.HTTP,
        login=None,
        password=None,
        health=ProxyHealth(
            total_conn_attemps=0,
            failed_conn_attemps=0,
            latency=None,
            last_tested=None,
        ),
    )


@pytest.mark.unit
@pytest.mark.asyncio
@patch("app.tasks.check_proxies.check_proxy_with_aws", new_callable=AsyncMock)
async def test_check_single_proxy_success(mock_check, proxy):
    mock_check.return_value = (True, 123)

    updated = await check_single_proxy(proxy)

    assert updated.health.total_conn_attemps == 1
    assert updated.health.failed_conn_attemps == 0
    assert updated.health.latency == 123
    assert isinstance(updated.health.last_tested, datetime.datetime)
    assert updated.health.last_tested.tzinfo == datetime.UTC


@pytest.mark.unit
@pytest.mark.asyncio
@patch("app.tasks.check_proxies.check_proxy_with_aws", new_callable=AsyncMock)
async def test_check_single_proxy_failure(mock_check, proxy):
    mock_check.return_value = (False, 0.0)

    updated = await check_single_proxy(proxy)

    assert updated.health.total_conn_attemps == 1
    assert updated.health.failed_conn_attemps == 1
    assert updated.health.latency is None
    assert updated.health.last_tested is None
