from ipaddress import IPv4Address
from unittest.mock import Mock, patch

import pytest
from geoip2.errors import AddressNotFoundError

from app.core.geoip import GeoIP
from app.models.proxy import Location


@pytest.fixture
def mock_reader():
    with patch("app.core.geoip.Reader") as mock_reader_cls:
        mock_reader = Mock()
        mock_reader_cls.return_value = mock_reader
        yield mock_reader


@pytest.mark.unit
@pytest.mark.asyncio
async def test_geoip_get_geolocation_success(mock_reader):
    # Arrange
    ip = IPv4Address("8.8.8.8")

    mock_response = Mock()
    mock_response.city.name = "Mountain View"
    mock_response.subdivisions.most_specific.name = "California"
    mock_response.country.iso_code = "US"
    mock_reader.city.return_value = mock_response

    geoip = GeoIP("dummy_path")

    # Act
    result = geoip.get_geolocation(ip)

    # Assert
    assert isinstance(result, Location)
    assert result.city == "Mountain View"
    assert result.region == "California"
    assert result.country_code == "US"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_geoip_get_geolocation_address_not_found(mock_reader):
    ip = IPv4Address("127.0.0.1")
    mock_reader.city.side_effect = AddressNotFoundError("Not found")

    geoip = GeoIP("dummy_path")
    result = geoip.get_geolocation(ip)

    assert result is None


@pytest.mark.parametrize(
    "city, region, country",
    [
        (None, "Region", "US"),
        ("City", None, "US"),
        ("City", "Region", None),
    ],
)
@pytest.mark.unit
@pytest.mark.asyncio
async def test_geoip_get_geolocation_incomplete_data(mock_reader, city, region, country):
    ip = IPv4Address("8.8.8.8")

    mock_response = Mock()
    mock_response.city.name = city
    mock_response.subdivisions.most_specific.name = region
    mock_response.country.iso_code = country
    mock_reader.city.return_value = mock_response

    geoip = GeoIP("dummy_path")
    result = geoip.get_geolocation(ip)

    assert result is None
