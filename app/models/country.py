from sqlalchemy import String as SA_String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Country(Base):
    """
    Represents a country using ISO codes.

    Attributes:
        code (str): ISO 3166-1 alpha-2 code (e.g., 'US', 'NL').
        name (str): Official name of the country in English.
    """

    __tablename__ = "countries"

    code: Mapped[str] = mapped_column(SA_String(2), index=True)
    name: Mapped[str] = mapped_column(unique=True)
