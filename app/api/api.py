from fastapi import APIRouter

from .v1.endpoints.country import router as country_router
from .v1.endpoints.proxy import router as proxy_router

api_router = APIRouter(prefix="/api")

api_router.include_router(country_router)
api_router.include_router(proxy_router)
