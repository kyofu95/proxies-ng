import datetime
from ipaddress import IPv4Address, IPv6Address
from unittest.mock import AsyncMock, patch

import pytest

from app.models.proxy import Protocol
from app.models.source import Source, SourceHealth
from app.service.source import SourceService
from app.tasks.fetch_proxies import (
    check_list_of_proxies,
    check_proxy,
    download_proxy_list,
    fetch_all_proxy_lists,
    try_parse_ip_port,
    validate_port,
)
from app.tasks.utils.network_request import HttpResult


@pytest.mark.unit
@pytest.mark.asyncio
@pytest.mark.parametrize("port", [1, 65535])
async def test_validate_port_valid(port):
    validate_port(port)  # Should not raise


@pytest.mark.unit
@pytest.mark.asyncio
@pytest.mark.parametrize("port", [0, 65536])
async def test_validate_port_invalid(port):
    with pytest.raises(ValueError):
        validate_port(port)


@pytest.mark.unit
@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("input_str", "expected"),
    [
        ("127.0.0.1:8080", (IPv4Address("127.0.0.1"), 8080)),
        ("http://192.168.1.1:3128", (IPv4Address("192.168.1.1"), 3128)),
        ("https://8.8.8.8:443", (IPv4Address("8.8.8.8"), 443)),
        ("10.0.0.1:0", None),  # invalid port
        ("10.0.0.1:65536", None),  # invalid port
    ],
)
async def test_valid_and_invalid_ip_port(input_str, expected):
    result = try_parse_ip_port(input_str)
    assert result == expected


@pytest.mark.unit
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "invalid_input",
    [
        "notanip:8080",
        "127.0.0.1:notaport",
        "http://:8080",
        "127.0.0.1",
        "127.0.0.1:8080:extra",
        "example.com:80",
        "2001:db8::1:1080",
        "socks5://2001:db8::2:3128",
    ],
)
async def test_invalid_inputs(invalid_input):
    assert try_parse_ip_port(invalid_input) is None


@pytest.mark.unit
@pytest.mark.asyncio
@patch("app.tasks.fetch_proxies.try_http_request")
async def test_download_proxy_list_success(mock_http_request):
    mock_http_request.return_value = AsyncMock(status=200, text="8.8.8.8:8080\ninvalid\n127.0.0.1:80")
    result = await download_proxy_list("http://example.com", Protocol.HTTP)
    assert result is not None
    assert len(result) == 1
    assert (IPv4Address("8.8.8.8"), 8080, Protocol.HTTP) in result
    # 127.0.0.1 is not global; invalid is ignored


@pytest.mark.unit
@pytest.mark.asyncio
@patch("app.tasks.fetch_proxies.try_http_request")
async def test_download_proxy_list_get_http_failure(mock_http_request):
    mock_http_request.return_value = None
    result = await download_proxy_list("http://bad-url.com", Protocol.HTTP)
    assert result is None


@pytest.mark.unit
@pytest.mark.asyncio
@patch("app.tasks.fetch_proxies.try_http_request")
async def test_download_proxy_list_get_http_status_failure(mock_http_request):
    mock_http_request.return_value = HttpResult(status=500, text="")
    result = await download_proxy_list("http://bad-url.com", Protocol.HTTP)
    assert result is None


@pytest.mark.unit
@pytest.mark.asyncio
@patch("app.tasks.fetch_proxies.check_proxy_with_aws", new_callable=AsyncMock)
async def test_check_proxy_valid(mock_check):
    mock_check.return_value = (True, 123)
    ip = IPv4Address("1.1.1.1")
    result = await check_proxy((ip, 8080), Protocol.HTTP)
    assert result[0] == ip
    assert result[1] == 8080
    assert result[2] == Protocol.HTTP
    assert isinstance(result[3], int)
    assert isinstance(result[4], datetime.datetime)


@pytest.mark.unit
@pytest.mark.asyncio
@patch("app.tasks.fetch_proxies.check_proxy_with_aws", new_callable=AsyncMock)
async def test_check_proxy_invalid(mock_check):
    mock_check.return_value = (False, 0)
    ip = IPv4Address("1.1.1.1")
    result = await check_proxy((ip, 8080), Protocol.HTTP)
    assert result is None


@pytest.mark.unit
@pytest.mark.asyncio
@patch("app.tasks.fetch_proxies.download_proxy_list", new_callable=AsyncMock)
@patch("app.service.source.SourceService.update", new_callable=AsyncMock)
async def test_fetch_all_proxy_lists_updates_source_health(mock_update, mock_download_proxy_list):
    mock_download_proxy_list.return_value = [(IPv4Address("8.8.8.8"), 8080, Protocol.HTTP)]

    source = Source(
        id=1,
        uri="http://example.com",
        uri_predefined_type=Protocol.HTTP,
        health=SourceHealth(id=222, total_conn_attempts=0, failed_conn_attempts=0, last_used=None),
    )

    source_service = SourceService(uow=AsyncMock())
    proxies = await fetch_all_proxy_lists([source], source_service)

    assert proxies == [(IPv4Address("8.8.8.8"), 8080, Protocol.HTTP)]
    assert source.health.total_conn_attempts == 1
    assert source.health.failed_conn_attempts == 0
    assert source.health.last_used is not None
    mock_update.assert_called_once_with(source)


@pytest.mark.unit
@pytest.mark.asyncio
@patch("app.tasks.fetch_proxies.download_proxy_list", new_callable=AsyncMock)
@patch("app.service.source.SourceService.update", new_callable=AsyncMock)
async def test_fetch_all_proxy_lists_failed_download_increments_failure(mock_update, mock_download_proxy_list):
    mock_download_proxy_list.return_value = None

    source = Source(
        id=1,
        uri="http://example.com",
        uri_predefined_type=Protocol.HTTP,
        health=SourceHealth(id=333, total_conn_attempts=0, failed_conn_attempts=0, last_used=None),
    )

    source_service = SourceService(uow=AsyncMock())
    proxies = await fetch_all_proxy_lists([source], source_service)

    assert proxies == []
    assert source.health.total_conn_attempts == 1
    assert source.health.failed_conn_attempts == 1
    assert source.health.last_used is not None
    mock_update.assert_called_once_with(source)


@pytest.mark.unit
@pytest.mark.asyncio
@patch("app.tasks.fetch_proxies.check_proxy", new_callable=AsyncMock)
async def test_check_list_of_proxies(mock_check_proxy):
    mock_check_proxy.side_effect = lambda ip, proto: (ip[0], ip[1], proto, 100, datetime.datetime.now(datetime.UTC))
    input_proxies = [(IPv4Address("1.1.1.1"), 8080, Protocol.HTTP)]
    result = await check_list_of_proxies(input_proxies)
    assert len(result) == 1
    assert result[0][0] == IPv4Address("1.1.1.1")
