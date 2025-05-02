from ipaddress import IPv4Address, IPv6Address, ip_address
from unittest.mock import AsyncMock, patch

import pytest

from app.tasks.utils.aws_check import (
    HTTP_STATUS_OK,
    Protocol,
    ProxyHttpResult,
    check_proxy_with_aws,
    format_proxy_url,
    try_aws_http_request_with_proxy,
    validate_aws_response,
)


@pytest.mark.unit
@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("address", "port", "protocol", "login", "password", "expected_result"),
    [
        (IPv4Address("127.0.0.1"), 8080, Protocol.HTTP, None, None, "http://127.0.0.1:8080"),
        (IPv4Address("127.0.0.1"), 8080, Protocol.SOCKS5, "user", "pass", "socks5://user:pass@127.0.0.1:8080"),
        (IPv4Address("127.0.0.1"), 1080, Protocol.HTTPS, None, None, "http://127.0.0.1:1080"),  # https -> http
    ],
)
async def test_format_proxy_url(address, port, protocol, login, password, expected_result):
    result = format_proxy_url(address, port, protocol, login, password)
    assert result == expected_result


@pytest.mark.unit
@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("address", "response_text", "response_status", "expected_result"),
    [
        (IPv4Address("127.0.0.1"), "127.0.0.1", HTTP_STATUS_OK, True),
        (IPv4Address("127.0.0.1"), "192.168.1.1", HTTP_STATUS_OK, False),
        (IPv4Address("127.0.0.1"), "127.0.0.1", 404, False),
        (IPv4Address("127.0.0.1"), "invalid_ip", HTTP_STATUS_OK, False),
    ],
)
async def test_validate_aws_response(address, response_text, response_status, expected_result):
    response = ProxyHttpResult(time=100, status=response_status, text=response_text)
    result = validate_aws_response(address, response)
    assert result == expected_result


@pytest.mark.unit
@pytest.mark.asyncio
@patch("app.tasks.utils.aws_check.try_http_request_with_proxy")
async def test_try_aws_http_request_with_proxy_success(mock_try_http):
    mock_try_http.return_value = ProxyHttpResult(
        status=200,
        text="1.2.3.4\n",
        time=123,
    )

    success, latency = await try_aws_http_request_with_proxy(
        ip_address("1.2.3.4"),
        "https://checkip.amazonaws.com/",
        "http://1.2.3.4:8080",
        Protocol.HTTP,
    )

    assert success is True
    assert latency == 123
    mock_try_http.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
@patch("app.tasks.utils.aws_check.try_http_request_with_proxy")
async def test_try_aws_http_request_with_proxy_ip_mismatch(mock_try_http):
    mock_try_http.return_value = ProxyHttpResult(
        status=200,
        text="5.6.7.8",
        time=100,
    )

    success, latency = await try_aws_http_request_with_proxy(
        ip_address("1.2.3.4"),
        "https://checkip.amazonaws.com/",
        "http://1.2.3.4:8080",
        Protocol.HTTP,
    )

    assert not success
    assert latency == 0


@pytest.mark.unit
@pytest.mark.asyncio
@patch("app.tasks.utils.aws_check.try_http_request_with_proxy")
async def test_try_aws_http_request_with_proxy_bad_status(mock_try_http):
    mock_try_http.return_value = ProxyHttpResult(
        status=500,
        text="1.2.3.4",
        time=100,
    )

    success, latency = await try_aws_http_request_with_proxy(
        ip_address("1.2.3.4"),
        "https://checkip.amazonaws.com/",
        "http://1.2.3.4:8080",
        Protocol.HTTP,
    )

    assert not success
    assert latency == 0


@pytest.mark.unit
@pytest.mark.asyncio
@patch("app.tasks.utils.aws_check.try_aws_http_request_with_proxy")
async def test_check_proxy_with_aws_success(mock_try_aws):
    mock_try_aws.side_effect = [
        (True, 150),  # first check
        (True, 160),  # second check
    ]

    success, latency = await check_proxy_with_aws(
        ip_address("1.2.3.4"),
        8080,
        Protocol.HTTP,
        delay=0,  # skip delay for test speed
    )

    assert success is True
    assert latency == 160
    assert mock_try_aws.call_count == 2


@pytest.mark.unit
@pytest.mark.asyncio
@patch("app.tasks.utils.aws_check.try_aws_http_request_with_proxy")
async def test_check_proxy_with_aws_fail_on_first(mock_try_aws):
    mock_try_aws.return_value = (False, 0)

    success, latency = await check_proxy_with_aws(
        ip_address("1.2.3.4"),
        8080,
        Protocol.HTTP,
        delay=0,  # skip delay for test speed
    )

    assert not success
    assert latency == 0
    assert mock_try_aws.call_count == 1


@pytest.mark.unit
@pytest.mark.asyncio
@patch("app.tasks.utils.aws_check.try_aws_http_request_with_proxy")
async def test_check_proxy_with_aws_fail_on_second(mock_try_aws):
    mock_try_aws.side_effect = [
        (True, 120),
        (False, 0),
    ]

    success, latency = await check_proxy_with_aws(
        ip_address("1.2.3.4"),
        8080,
        Protocol.HTTP,
        delay=0,  # skip delay for test speed
    )

    assert not success
    assert latency == 0
    assert mock_try_aws.call_count == 2
