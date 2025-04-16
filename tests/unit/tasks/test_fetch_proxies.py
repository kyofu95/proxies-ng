import pytest
from ipaddress import IPv4Address, IPv6Address

from app.tasks.fetch_proxies import try_parse_ip_port


@pytest.mark.unit
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "input_str,expected",
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
