from ipaddress import IPv4Address, IPv6Address

from pydantic import BaseModel, ConfigDict, Field

from app.models.proxy import Protocol


class ProxyAddressResponse(BaseModel):
    """
    Represents the geographical location of a proxy address.

    Attributes:
        country (str): Country name.
        region (str): Region or state.
        city (str): City name.
    """

    country: str
    region: str
    city: str

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

    model_config = ConfigDict(from_attributes=True)
