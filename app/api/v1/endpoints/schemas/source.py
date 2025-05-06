from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, HttpUrl, TypeAdapter

from app.models.proxy import Protocol
from app.models.source import SourceType

http_url_adapter = TypeAdapter(HttpUrl)
# Url: validate as HttpUrl, but store as str
Url = Annotated[str, BeforeValidator(lambda value: str(http_url_adapter.validate_python(value)))]


class SourceHealthResponse(BaseModel):
    """
    Represents health metrics for a proxy source.

    Attributes:
        total_conn_attemps (int): Total number of connection attempts to this source.
        failed_conn_attemps (int): Number of failed connection attempts.
        last_used (datetime | None): Timestamp of the last successful usage, if any.
    """

    total_conn_attemps: int
    failed_conn_attemps: int

    last_used: datetime | None = Field(default=None)

    model_config = ConfigDict(from_attributes=True)


class SourceName(BaseModel):
    """
    Base model representing only the name of a source.

    Attributes:
        name (str): Name of the source.
    """

    name: str


class Source(SourceName):
    """
    Full model representing a proxy source with metadata.

    Attributes:
        uri (Url): Source URI (validated as a proper HTTP/HTTPS URL).
        uri_predefined_type (Protocol | None): Optional protocol if predefined.
        type (SourceType): Type of the source (e.g., json, txt).
    """

    uri: Url
    uri_predefined_type: Protocol | None = Field(default=None)
    type: SourceType

    model_config = ConfigDict(from_attributes=True)


class SourceNameRequest(SourceName):
    """Request model for operations involving just the source name (e.g., filtering)."""


class SourceRequest(Source):
    """
    Request model for creating or updating a source.

    Inherits all fields from Source.
    """


class SourceResponse(Source):
    """
    Response model representing a full source with its health information.

    Attributes:
        health (SourceHealthResponse): Health stats related to this source.
    """

    health: SourceHealthResponse
