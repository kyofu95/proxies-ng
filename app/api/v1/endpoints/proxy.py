from typing import Annotated

from fastapi import APIRouter, Query, status
from pydantic import TypeAdapter

from app.models.proxy import Protocol

from .schemas.proxy import PaginatedProxyResponse, ProxyResponse
from .utils.dependencies import ProxyServiceDep

router = APIRouter(prefix="/proxy", tags=["Proxy"])

proxy_response_adapter = TypeAdapter(list[ProxyResponse])


@router.get("/", response_model_exclude_none=True, status_code=status.HTTP_200_OK)
async def get_proxies(
    proxy_service: ProxyServiceDep,
    country_code: Annotated[
        str | None,
        Query(..., description="2-letter country code", min_length=2, max_length=2),
    ] = None,
    protocol: Annotated[Protocol | None, Query(...)] = None,
    offset: Annotated[int | None, Query(ge=0)] = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> PaginatedProxyResponse:
    """
    Retrieve a paginated list of available proxies.

    This endpoint fetches proxies from the database with optional filtering by country code.
    Only proxies that have been checked (i.e. tested at least once) are returned.
    The results can be paginated using `offset` and `limit`.

    Args:
        proxy_service (ProxyServiceDep): Injected ProxyService dependency.
        country_code (str | None): Optional 2-letter ISO 3166-1 Alpha-2 country code to filter proxies by.
        protocol (Protocol | None): Optional protocol to filter proxies by (e.g., HTTP, SOCKS5).
        offset (int | None): Optional number of items to skip before returning results.
        limit (int): Maximum number of proxies to return. Defaults to 100.

    Returns:
        PaginatedProxyResponse: A paginated response containing a list of proxies and metadata.
    """
    proxies = await proxy_service.get_proxies(
        protocol=protocol,
        country_alpha2_code=country_code,
        only_checked=True,
        offset=offset,
        limit=limit,
    )
    validated_proxies = proxy_response_adapter.validate_python(proxies)

    total_count = await proxy_service.get_proxies_count(
        protocol=protocol,
        country_alpha2_code=country_code,
        only_checked=True,
    )

    return PaginatedProxyResponse(proxies=validated_proxies, total=total_count, offset=offset, limit=limit)
