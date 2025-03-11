from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI


@asynccontextmanager
async def app_lifespan(_: FastAPI) -> AsyncIterator[None]:
    """
    Define the application's lifespan for startup and shutdown events.

    This function is used to manage application-level lifecycle events, such as
    initializing resources on startup or cleaning up resources during shutdown.

    Args:
        _ (FastAPI): The FastAPI application instance. Currently omitted.

    Yields:
        None: Indicates no additional setup or teardown logic is required.
    """
    yield


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    This function sets up the FastAPI instance, includes API routes, and applies
    any necessary application-wide configurations.

    Returns:
        FastAPI: The configured FastAPI application instance.
    """
    api = FastAPI(
        title="Proxies-NG",
        version="0.1",
        openapi_url=None,
        docs_url=None,
        redoc_url=None,
        lifespan=app_lifespan,
    )

    return api


app = create_app()
"""The main FastAPI application instance."""
