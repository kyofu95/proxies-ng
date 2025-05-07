from pydantic import BaseModel


class HealthResponse(BaseModel):
    """
    Response model for health check endpoint.

    Attributes:
        status (str): The current status of the application, e.g., "ok" or "failure".
    """

    status: str
