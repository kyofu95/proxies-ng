import typing

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import HTMLResponse, JSONResponse
from starlette.types import ExceptionHandler as StarletteExceptionHandler

from app.core.exceptions import AlreadyExistsError

from .views.pages import templates


async def not_found_exception_handler(request: Request, _: HTTPException) -> JSONResponse | HTMLResponse:
    """
    Handle 404 Not Found errors.

    This function handles requests that result in a 404 error. It checks whether
    the request is for an API endpoint or a regular page. If the request is for
    an API, it returns a JSON response with a detail message. If the request is
    for a regular page, it returns an HTML 404 page.

    Args:
        request (Request): The incoming request object.
        _ (HTTPException): The HTTPException that triggered the error.

    Returns:
        JSONResponse | HTMLResponse: The appropriate response (JSON or HTML) based on the request type.
    """
    # check if url string contains 'api'
    api_index = request.url.path.find("/api/")
    if api_index != -1:
        # if api, return json response
        content = {"detail": "Not Found"}
        return JSONResponse(content, status_code=status.HTTP_404_NOT_FOUND)

    # if web interface, return 404 web page
    context = {"request": request}
    return templates.TemplateResponse("404.html", context=context, status_code=status.HTTP_404_NOT_FOUND)


async def already_exists_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    """
    Handle AlreadyExistsError exceptions.

    Returns a 409 Conflict response with a descriptive message.

    Args:
        _ (Request): The incoming request object.
        exc (HTTPException): The AlreadyExistsError exception.

    Returns:
        JSONResponse: JSON response with error details and 409 status.
    """
    content = {"detail": str(exc)}
    return JSONResponse(content=content, status_code=status.HTTP_409_CONFLICT)


def install_exception_handlers(api: FastAPI) -> None:
    """
    Install custom exception handlers for the FastAPI application.

    Installs a handler for:
    - 404 Not Found errors.
    - AlreadyExistsError exceptions.

    Args:
        api (FastAPI): The FastAPI application instance to install exception handlers on.

    Returns:
        None
    """
    # i give up. i have no idea what type is StarletteExceptionHandler, so i simply cast to it
    api.add_exception_handler(
        status.HTTP_404_NOT_FOUND,
        typing.cast(StarletteExceptionHandler, not_found_exception_handler),
    )

    api.add_exception_handler(
        AlreadyExistsError,
        typing.cast(StarletteExceptionHandler, already_exists_exception_handler),
    )
