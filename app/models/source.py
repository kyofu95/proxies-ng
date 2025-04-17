from __future__ import annotations

from datetime import datetime
from enum import IntEnum
from uuid import UUID

from sqlalchemy import DateTime as SA_DateTime
from sqlalchemy import Enum as SA_Enum
from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .proxy import Protocol


class SourceType(IntEnum):
    """
    Enumeration of proxy source types.

    Attributes:
        Text (int): Represents a text-based source.
    """

    Text = 1


class SourceHealth(Base):
    """
    Tracks the connection health of a source.

    Attributes:
        total_conn_attempts (int): Total number of connection attempts.
        failed_conn_attempts (int): Number of failed connection attempts.
        last_used (datetime | None): Timestamp of the last time the source was used.
        source_id (UUID): Foreign key linking to the associated source.
        source (Source): Relationship to the Source model.
    """

    __tablename__ = "sources_health"
    __table_args__ = (
        UniqueConstraint(
            "source_id",
        ),  # sqlalchemy recommends to use constraint on fk in one-to-one
    )

    total_conn_attemps: Mapped[int]
    failed_conn_attemps: Mapped[int]

    last_used: Mapped[datetime | None] = mapped_column(SA_DateTime(timezone=True))

    source_id: Mapped[UUID] = mapped_column(ForeignKey("sources.id"))
    source: Mapped[Source] = relationship(back_populates="health", single_parent=True)


class Source(Base):
    """
    Represents a source of data.

    Attributes:
        name (str): The name of the source.
        uri (str): The URI where the source data can be accessed.
        uri_predefined_type (Protocol | None): Optional predefined protocol type for the URI.
        resource (Resource): The type of resource provided by the source.
        health (SourceHealth): Relationship to the SourceHealth model.
    """

    __tablename__ = "sources"

    name: Mapped[str] = mapped_column(index=True)
    uri: Mapped[str]
    uri_predefined_type: Mapped[Protocol | None] = mapped_column(
        SA_Enum(Protocol, values_callable=lambda obj: [e.name for e in obj]),
        default=None,
    )
    type: Mapped[SourceType] = mapped_column(
        SA_Enum(SourceType, values_callable=lambda obj: [e.name for e in obj]),
    )

    health: Mapped[SourceHealth | None] = relationship(
        back_populates="source",
        cascade="all, delete-orphan",
        lazy="joined",
    )
