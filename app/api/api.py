from fastapi import APIRouter

from .v1.endpoints.auth import router as auth_router
from .v1.endpoints.country import router as country_router
from .v1.endpoints.health import router as health_router
from .v1.endpoints.proxy import router as proxy_router
from .v1.endpoints.source import router as source_router
from .v1.endpoints.user import router as user_router

api_router = APIRouter(prefix="/api")

# public apis
api_router.include_router(country_router)
api_router.include_router(proxy_router)
api_router.include_router(health_router)

private_api_router = APIRouter(prefix="/private")

# private apis
private_api_router.include_router(auth_router)
private_api_router.include_router(source_router)
private_api_router.include_router(user_router)

api_router.include_router(private_api_router)
