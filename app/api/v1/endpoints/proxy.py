from typing import Annotated

from fastapi import APIRouter, Query, status
from pydantic import TypeAdapter

from .schemas.proxy import ProxyResponse
from .utils.di_deps import ProxyServiceDep

router = APIRouter(prefix="/proxy", tags=["Proxy"])


@router.get("/", response_model_exclude_none=True, status_code=status.HTTP_200_OK)
async def get_proxies(
    proxy_service: ProxyServiceDep,
    country_code: Annotated[
        str | None,
        Query(..., description="2-letter country code", min_length=2, max_length=2),
    ] = None,
) -> list[ProxyResponse]:
    """
    Retrieve a list of available proxies.

    This endpoint fetches all stored proxies from the database.
    It can filter the proxies by the 2-letter country code and only return those marked as "checked".

    Args:
        proxy_service (ProxyServiceDep): Injected ProxyService dependency.
        country_code (str | None): Optional 2-letter country code to filter proxies by country.
            If not provided, all proxies will be returned.

    Returns:
        list[ProxyResponse]: A list of proxy objects with their connection and geolocation info.
    """
    type_adapter = TypeAdapter(list[ProxyResponse])

    proxies = await proxy_service.get_proxies(country_alpha2_code=country_code, only_checked=True)
    return type_adapter.validate_python(proxies)
