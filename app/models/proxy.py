from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from ipaddress import IPv4Address, IPv6Address
from typing import NamedTuple
from uuid import UUID

from sqlalchemy import DateTime as SA_DateTime
from sqlalchemy import Enum as SA_Enum
from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .country import Country


class Location(NamedTuple):
    """
    Represents a geographic location.

    Attributes:
        city (str): The name of the city.
        region (str): The name of the region or state.
        country_code (str): The name of the country in 3166-1 Alpha-2 format.
    """

    city: str
    region: str
    country_code: str


class Protocol(StrEnum):
    """
    Enumeration of supported proxy protocols.

    Attributes:
        HTTP (str): HTTP protocol.
        HTTPS (str): HTTPS protocol.
        SOCKS4 (str): SOCKS4 protocol.
        SOCKS5 (str): SOCKS5 protocol.
    """

    HTTP = "HTTP"
    HTTPS = "HTTPS"
    SOCKS4 = "SOCKS4"
    SOCKS5 = "SOCKS5"


class ProxyAddress(Base):
    """
    Represents the geographical address associated with a proxy.

    Attributes:
        country_code (UUID): Foreign key to countries.id.
        country (Country): Relationship to the Country model..
        region (str): Region or state of the proxy's location.
        city (str): City of the proxy's location.
    """

    __tablename__ = "proxies_address"
    __table_args__ = (UniqueConstraint("country_id", "region", "city"),)

    country_id: Mapped[UUID] = mapped_column(ForeignKey("countries.id", ondelete="RESTRICT"))
    country: Mapped[Country] = relationship(lazy="joined")

    region: Mapped[str]
    city: Mapped[str]


class ProxyHealth(Base):
    """
    Tracks the connection health of a proxy.

    Attributes:
        total_conn_attempts (int): Total number of connection attempts.
        failed_conn_attempts (int): Number of failed connection attempts.
        latency (int): Last measured latency in milliseconds.
        last_tested (datetime | None): Timestamp of the last connection test.
        proxy_id (UUID): Foreign key linking to the proxy id.
        proxy (Proxy): Relationship to the Proxy model.
    """

    __tablename__ = "proxies_health"
    __table_args__ = (
        UniqueConstraint(
            "proxy_id",
        ),  # sqlalchemy recommends to use constraint on fk in one-to-one
    )

    total_conn_attempts: Mapped[int] = mapped_column(default=0)
    failed_conn_attempts: Mapped[int] = mapped_column(default=0)

    latency: Mapped[int] = mapped_column(default=0)

    last_tested: Mapped[datetime | None] = mapped_column(SA_DateTime(timezone=True))

    proxy_id: Mapped[UUID] = mapped_column(ForeignKey("proxies.id"))
    proxy: Mapped[Proxy] = relationship(back_populates="health", single_parent=True)


class Proxy(Base):
    """
    Represents a proxy and its associated metadata.

    Attributes:
        address (IPv4Address | IPv6Address): IP address of the proxy.
        port (int): Port on which the proxy is listening.
        protocol (Protocol): Communication protocol used by the proxy.
        login (str | None): Optional login credential for the proxy.
        password (str | None): Optional password credential for the proxy.
        geo_address_id (UUID | None) : Foreign key linking to the ProxyAddress id.
        geo_address (ProxyAddress | None): Relationship to the ProxyAddress model.
        health (ProxyHealth): Relationship to the ProxyHealth model.
    """

    __tablename__ = "proxies"
    __table_args__ = (UniqueConstraint("address", "port", "protocol"),)

    address: Mapped[IPv4Address | IPv6Address] = mapped_column(INET)
    port: Mapped[int]
    protocol: Mapped[Protocol] = mapped_column(
        SA_Enum(Protocol, values_callable=lambda obj: [e.name for e in obj]),
    )

    login: Mapped[str | None] = mapped_column(default=None)
    password: Mapped[str | None] = mapped_column(default=None)

    geo_address_id: Mapped[UUID | None] = mapped_column(ForeignKey("proxies_address.id", ondelete="RESTRICT"))
    geo_address: Mapped[ProxyAddress | None] = relationship(
        lazy="joined",
    )
    health: Mapped[ProxyHealth] = relationship(
        back_populates="proxy",
        cascade="all, delete-orphan",
        lazy="joined",
    )
