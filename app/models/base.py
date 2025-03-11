from uuid import UUID

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """
    Base class for SQLAlchemy declarative models with predefined naming conventions for Alembic migrations.

    Attributes:
        metadata (MetaData): An instance of SQLAlchemy's MetaData, configured with naming
            conventions for Alembic migrations.

    Notes:
        This class should be subclassed and used as a base for other declarative class definitions.
    """

    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        },
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
