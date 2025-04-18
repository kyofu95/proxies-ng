from pydantic import BaseModel, ConfigDict, Field


class CountryCodeResponse(BaseModel):
    """
    Country response model.

    Attributes:
        code (str): ISO 3166-1 Alpha-2 country code.
    """

    code: str = Field(..., min_length=2, max_length=2)

    model_config = ConfigDict(from_attributes=True)


class CountryResponse(CountryCodeResponse):
    """
    Country response model.

    Attributes:
        name (str): Full country name.
    """

    name: str

    model_config = ConfigDict(from_attributes=True)
