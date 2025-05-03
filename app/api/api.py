from fastapi import APIRouter

from .v1.endpoints.auth import router as auth_router
from .v1.endpoints.country import router as country_router
from .v1.endpoints.proxy import router as proxy_router

api_router = APIRouter(prefix="/api")

api_router.include_router(country_router)
api_router.include_router(proxy_router)

private_api_router = APIRouter(prefix="/private")

private_api_router.include_router(auth_router)

api_router.include_router(private_api_router)
