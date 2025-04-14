from fastapi import APIRouter, status
from pydantic import TypeAdapter

from .schemas.proxy import ProxyResponse
from .utils.di_deps import ProxyServiceDep

router = APIRouter(prefix="/proxy", tags=["Proxy"])


@router.get("/", response_model_exclude_none=True, status_code=status.HTTP_200_OK)
async def get_proxies(proxy_service: ProxyServiceDep) -> list[ProxyResponse]:
    """
    Retrieve a list of available proxies.

    This endpoint fetches all stored proxies from the database using the ProxyService.
    It filters out any `None` values in the response.

    Args:
        proxy_service (ProxyServiceDep): Injected ProxyService dependency.

    Returns:
        list[ProxyResponse]: A list of proxy objects with their connection and geolocation info.
    """
    type_adapter = TypeAdapter(list[ProxyResponse])

    proxies = await proxy_service.get_proxies(only_checked=True)
    return type_adapter.validate_python(proxies)
