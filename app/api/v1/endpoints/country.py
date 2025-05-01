from fastapi import APIRouter, status

from .utils.dependencies import ProxyServiceDep

router = APIRouter(prefix="/country", tags=["country"])


@router.get("/", status_code=status.HTTP_200_OK)
async def get_countries(proxy_service: ProxyServiceDep) -> list[str]:
    """
    Retrieve a list of available countries.

    Args:
        proxy_service (ProxyServiceDep): The injected ProxyService dependency responsible for fetching the countries.

    Returns:
        list[str]: A list of country names or codes.
    """
    return await proxy_service.get_countries()
