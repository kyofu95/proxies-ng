from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import TypeAdapter

from .schemas.source import SourceNameRequest, SourceRequest, SourceResponse
from .schemas.status import StatusMessageResponse
from .utils.dependencies import SourceServiceDep
from .utils.token_auth import get_current_user_from_cookie

router = APIRouter(prefix="/source")

source_response_adapter = TypeAdapter(list[SourceResponse])


@router.get("/all", status_code=status.HTTP_200_OK, dependencies=[Depends(get_current_user_from_cookie)])
async def get_all_sources(source_service: SourceServiceDep) -> list[SourceResponse]:
    """
    Get a list of all available sources.

    This endpoint requires the user to be authenticated. The dependency 'get_current_user_from_cookie'
    ensures that the request includes a valid access token.

    Args:
        source_service (SourceServiceDep): Service for handling source-related operations.

    Returns:
        list[SourceResponse]: A list of all sources in the system.
    """
    sources = await source_service.get_sources()

    return source_response_adapter.validate_python(sources)


@router.post("/", status_code=status.HTTP_201_CREATED, dependencies=[Depends(get_current_user_from_cookie)])
async def add_source(
    new_source: SourceRequest,
    source_service: SourceServiceDep,
) -> StatusMessageResponse:
    """
    Add a new source to the system.

    This endpoint requires the user to be authenticated. The dependency 'get_current_user_from_cookie'
    ensures that the request includes a valid access token.

    Args:
        new_source (SourceRequest): The source data to create.
        source_service (SourceServiceDep): Service for handling source-related operations.

    Returns:
        StatusMessageResponse: A response indicating successful creation.
    """
    await source_service.create(
        name=new_source.name,
        url=new_source.uri,
        uri_type=new_source.uri_predefined_type,
    )

    return StatusMessageResponse(detail="created successfully")


@router.delete("/", status_code=status.HTTP_202_ACCEPTED, dependencies=[Depends(get_current_user_from_cookie)])
async def remove_source(
    source: SourceNameRequest,
    source_service: SourceServiceDep,
) -> StatusMessageResponse:
    """
    Remove an existing source by its name.

    This endpoint requires the user to be authenticated. The dependency 'get_current_user_from_cookie'
    ensures that the request includes a valid access token.

    Args:
        source (SourceNameRequest): The name of the source to remove.
        source_service (SourceServiceDep): Service for handling source-related operations.

    Raises:
        HTTPException: If the source with the specified name is not found.

    Returns:
        StatusMessageResponse: A response indicating successful deletion.
    """
    source_to_remove = await source_service.get_by_name(name=source.name)
    if not source_to_remove:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="source with such name doesnt exist")

    await source_service.remove(source_to_remove)

    return StatusMessageResponse(detail="deleted successfully")
