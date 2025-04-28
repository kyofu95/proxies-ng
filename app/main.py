from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.api import api_router
from app.views.pages import router as pages_router

from .error_handlers import install_exception_handlers

BASE_PATH = Path(__file__).resolve().parent


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

    api.mount(
        "/static",
        StaticFiles(directory=str(BASE_PATH / "static")),
        name="static",
    )

    api.include_router(pages_router)
    api.include_router(api_router)

    install_exception_handlers(api)

    return api


app = create_app()
"""The main FastAPI application instance."""
