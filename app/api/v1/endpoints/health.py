import asyncio

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import text as sa_text

from .schemas.health import HealthResponse
from .utils.dependencies import UnitOfWorkDep

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("/", status_code=status.HTTP_200_OK)
async def health_check(unit_of_work: UnitOfWorkDep) -> HealthResponse:
    """
    Health check endpoint.

    Verifies database connectivity by executing a simple SQL query
    with a 1-second timeout. If the query times out, an HTTP 503
    service unavailable error is raised, indicating a backend failure.

    Args:
        unit_of_work (UnitOfWorkDep): Dependency that provides a SQLAlchemy unit of work.

    Raises:
        HTTPException: If the database does not respond within the timeout,
            a 503 Service Unavailable error is raised with a detail message.

    Returns:
        HealthResponse: A response indicating the service is healthy with status "ok".
    """
    async with unit_of_work as uow:
        try:
            await asyncio.wait_for(uow.session.execute(sa_text("SELECT 1")), timeout=1)
        except TimeoutError as exc:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="backend failure") from exc

    return HealthResponse(status="ok")
