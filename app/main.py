import logging
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from asgi_correlation_id import CorrelationIdFilter, CorrelationIdMiddleware
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from prometheus_fastapi_instrumentator import Instrumentator

from app.api.api import api_router
from app.core.config import common_settings
from app.views.pages import router as pages_router

from .error_handlers import install_exception_handlers

logger = logging.getLogger(__name__)

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


def init_logger() -> None:
    """Initialize and configure the application logger."""
    logger = logging.getLogger(__name__)

    formatter = logging.Formatter(
        "%(asctime)s [%(processName)s: %(process)d] [%(levelname)s] [%(correlation_id)s] %(name)s: %(message)s",
    )

    cid_filter = CorrelationIdFilter(uuid_length=32)

    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)
    console.addFilter(cid_filter)

    logger.addHandler(console)

    if common_settings.debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    This function sets up the FastAPI instance, includes API routes, and applies
    any necessary application-wide configurations.

    Returns:
        FastAPI: The configured FastAPI application instance.
    """
    init_logger()

    logger = logging.getLogger(__name__)
    logger.info("Application startup")

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

    # setup correlation id
    api.add_middleware(CorrelationIdMiddleware)

    api.add_middleware(
        CORSMiddleware,
        allow_origins=common_settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["X-Requested-With", "X-Request-ID"],
        expose_headers=["X-Request-ID"],
    )

    # setup metrics
    Instrumentator().instrument(api, metric_subsystem="fastapi").expose(api)

    return api


app = create_app()
"""The main FastAPI application instance."""
