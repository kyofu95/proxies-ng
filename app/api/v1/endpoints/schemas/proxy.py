from datetime import datetime
from ipaddress import IPv4Address, IPv6Address

from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.models.proxy import Protocol

from .country import CountryResponse


class ProxyAddressResponse(BaseModel):
    """
    Proxy address response model with geolocation data.

    Attributes:
        region (str): Name of the region.
        city (str): Name of the city.
        country (CountryResponse): Associated country information (excluded from output).
    """

    @computed_field
    def country_iso_code(self) -> str:
        """
        ISO 3166-1 Alpha-2 country code from related country object.

        Returns:
            str: Country code.
        """
        return self.country.code

    region: str
    city: str
    country: CountryResponse = Field(exclude=True)

    model_config = ConfigDict(from_attributes=True)


class ProxyHealthResponse(BaseModel):
    """
    Proxy health status information.

    Attributes:
        latency (int): Measured latency in milliseconds.
        last_tested (datetime): Timestamp of the last proxy test.
    """

    latency: int
    last_tested: datetime

    model_config = ConfigDict(from_attributes=True)


class ProxyResponse(BaseModel):
    """
    Represents the full proxy response with connection and geolocation details.

    Attributes:
        ip (IPv4Address | IPv6Address): IP address of the proxy.
        port (int): Port number the proxy is running on.
        protocol (Protocol): Protocol type (e.g., HTTP, SOCKS5).
        login (str | None): Optional login credential for the proxy.
        password (str | None): Optional password credential for the proxy.
        geoaddress (ProxyAddressResponse): Geolocation info for the proxy IP.
    """

    ip: IPv4Address | IPv6Address = Field(alias="address", serialization_alias="ip")
    port: int
    protocol: Protocol
    login: str | None = Field(default=None)
    password: str | None = Field(default=None)
    geoaddress: ProxyAddressResponse = Field(alias="geo_address", serialization_alias="geoaddress")
    health: ProxyHealthResponse

    model_config = ConfigDict(from_attributes=True)


class PaginatedProxyResponse(BaseModel):
    """
    Paginated response model for proxies.

    Represents a paginated list of proxy responses along with metadata
    such as total count, offset, and limit for pagination control.

    Attributes:
        proxies (list[ProxyResponse]): A list of proxy response objects.
        total (int): Total number of proxies available matching the query.
        offset (int | None): The starting index of the returned items.
        limit (int): The maximum number of items returned.
    """

    proxies: list[ProxyResponse]
    total: int
    offset: int | None
    limit: int
