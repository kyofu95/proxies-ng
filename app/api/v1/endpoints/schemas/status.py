from pydantic import BaseModel


class StatusMessage(BaseModel):
    """
    Generic status message used for simple API responses.

    Attributes:
        detail (str): A human-readable message describing the status or result of the operation.
    """

    detail: str


# Alias for use in route responses to clarify intent
StatusMessageResponse = StatusMessage
