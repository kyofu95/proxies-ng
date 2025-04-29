from datetime import datetime, timezone

from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class User(Base):
    """
    Represents a user in the system.

    Attributes:
        login (str): Unique username used for authentication.
        password (str): Hashed password for the user.
        created_at (datetime): Timestamp when the user was created.
        updated_at (datetime | None): Timestamp of the last update to the user record.
        active (bool): Indicates whether the user account is active.
    """

    __tablename__ = "users"

    login: Mapped[str] = mapped_column(index=True, unique=True)
    password: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
    )
    active: Mapped[bool] = mapped_column(default=True)
