from fastapi import APIRouter, status
from pydantic import TypeAdapter

from .schemas.source import SourceNameRequest, SourceRequest, SourceResponse
from .utils.dependencies import SourceServiceDep
from .utils.token_auth import CurrentUserDep

router = APIRouter(prefix="/source")


@router.get("/all", status_code=status.HTTP_200_OK)
async def get_all_sources(user: CurrentUserDep, source_service: SourceServiceDep) -> list[SourceResponse]:
    """
    Get a list of all available sources.

    Args:
        user (CurrentUserDep): The currently authenticated user.
        source_service (SourceServiceDep): Service for handling source-related operations.

    Returns:
        list[SourceResponse]: A list of all sources in the system.
    """
    type_adapter = TypeAdapter(list[SourceResponse])

    sources = await source_service.get_sources()

    return type_adapter.validate_python(sources)


@router.post("/", status_code=status.HTTP_201_CREATED)
async def add_source(new_source: SourceRequest, user: CurrentUserDep, source_service: SourceServiceDep) -> None:
    """
    Add a new source to the system.

    Args:
        new_source (SourceRequest): The source data to create.
        user (CurrentUserDep): The currently authenticated user.
        source_service (SourceServiceDep): Service for handling source-related operations.

    Returns:
        None
    """
    await source_service.create(
        name=new_source.name,
        url=new_source.uri,
        uri_type=new_source.uri_predefined_type,
    )


@router.delete("/", status_code=status.HTTP_202_ACCEPTED)
async def remove_source(source: SourceNameRequest, user: CurrentUserDep, source_service: SourceServiceDep) -> None:
    """
    Remove an existing source by its name.

    Args:
        source (SourceNameRequest): The name of the source to remove.
        user (CurrentUserDep): The currently authenticated user.
        source_service (SourceServiceDep): Service for handling source-related operations.

    Returns:
        None
    """
    source_to_remove = await source_service.get_by_name(name=source.name)
    if source_to_remove:
        await source_service.remove(source_to_remove)
