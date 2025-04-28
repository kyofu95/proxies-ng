from ipaddress import IPv4Address, IPv6Address

import pytest

from app.tasks.utils.aws_check import HTTP_STATUS_OK, Protocol, ProxyHttpResult, format_proxy_url, validate_aws_response


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
