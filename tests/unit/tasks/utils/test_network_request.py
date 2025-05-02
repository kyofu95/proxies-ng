import asyncio
from unittest.mock import AsyncMock, patch

import pytest
from aioresponses import aioresponses

from aiohttp.client_exceptions import ClientError
from aiohttp_socks import ProxyError

from app.models.proxy import Protocol
from app.tasks.utils.network_request import (
    HttpResult,
    ProxyHttpResult,
    graceful_shutdown,
    try_http_request,
    try_http_request_with_proxy,
)


@pytest.mark.unit
@pytest.mark.asyncio
@patch("app.tasks.utils.network_request.asyncio.sleep", new_callable=AsyncMock)
async def test_graceful_shutdown_https_protocol(mock_sleep):
    await graceful_shutdown(Protocol.HTTPS)
    mock_sleep.assert_awaited_once_with(0.250)


@pytest.mark.unit
@pytest.mark.asyncio
@patch("app.tasks.utils.network_request.asyncio.sleep", new_callable=AsyncMock)
async def test_graceful_shutdown_other_protocols(mock_sleep):
    await graceful_shutdown(Protocol.HTTP)
    mock_sleep.assert_awaited_once_with(0)


@pytest.mark.unit
@pytest.mark.asyncio
@patch("app.tasks.utils.network_request.asyncio.sleep", new_callable=AsyncMock)
async def test_graceful_shutdown_no_protocol(mock_sleep):
    await graceful_shutdown(None)
    mock_sleep.assert_awaited_once_with(0)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_try_http_request_with_proxy_http_success_http():
    url = "http://example.com"
    proxy_url = "http://127.0.0.1:8080"
    expected_text = "Proxy OK"

    with aioresponses() as mock:
        mock.get(url, status=200, body=expected_text)

        result = await try_http_request_with_proxy(
            url=url, proxy_url=proxy_url, protocol=Protocol.HTTP, proxy_timeout=1
        )

        assert isinstance(result, ProxyHttpResult)
        assert result.status == 200
        assert result.text == expected_text
        assert isinstance(result.time, int)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_try_http_request_with_proxy_http_success_socks4():
    url = "http://example.com"
    proxy_url = "http://127.0.0.1:8080"
    expected_text = "Proxy OK"

    with aioresponses() as mock:
        mock.get(url, status=200, body=expected_text)

        result = await try_http_request_with_proxy(
            url=url, proxy_url=proxy_url, protocol=Protocol.SOCKS4, proxy_timeout=1
        )

        assert isinstance(result, ProxyHttpResult)
        assert result.status == 200
        assert result.text == expected_text
        assert isinstance(result.time, int)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_try_http_request_with_proxy_failure_connection_error_exc():
    url = "http://example.com"
    proxy_url = "http://127.0.0.1:8080"

    with aioresponses() as mock:
        mock.get(url, exception=ConnectionError())

        result = await try_http_request_with_proxy(
            url=url, proxy_url=proxy_url, protocol=Protocol.HTTP, proxy_timeout=1
        )

        assert result is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_try_http_request_with_proxy_proxy_failure_exc():
    url = "http://example.com"
    proxy_url = "http://127.0.0.1:8080"

    with aioresponses() as mock:
        mock.get(url, exception=ProxyError("Proxy failure"))

        result = await try_http_request_with_proxy(
            url=url, proxy_url=proxy_url, protocol=Protocol.SOCKS4, proxy_timeout=1
        )

        assert result is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_try_http_request_with_proxy_client_exc():
    url = "http://example.com"
    proxy_url = "http://127.0.0.1:8080"

    with aioresponses() as mock:
        mock.get(url, exception=ClientError("Client error"))

        result = await try_http_request_with_proxy(
            url=url, proxy_url=proxy_url, protocol=Protocol.SOCKS4, proxy_timeout=1
        )

        assert result is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_try_http_request_with_proxy_undef_exc():
    url = "http://example.com"
    proxy_url = "http://127.0.0.1:8080"

    with aioresponses() as mock:
        mock.get(url, exception=RuntimeError("undefined error"))

        result = await try_http_request_with_proxy(
            url=url, proxy_url=proxy_url, protocol=Protocol.SOCKS4, proxy_timeout=1
        )

        assert result is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_try_http_request_success():
    url = "http://example.com"
    expected_text = "Hello, World!"

    with aioresponses() as mock:
        mock.get(url, status=200, body=expected_text)

        result = await try_http_request(url)

        assert isinstance(result, HttpResult)
        assert result.status == 200
        assert result.text == expected_text


@pytest.mark.unit
@pytest.mark.asyncio
async def test_try_http_request_failure():
    url = "http://example.com"

    with aioresponses() as mock:
        mock.get(url, exception=ConnectionError())

        result = await try_http_request(url)

        assert result is None
