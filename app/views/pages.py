from pathlib import Path

from fastapi import APIRouter, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from .utils.user_deps import IsLoggedDep

BASE_PATH = Path(__file__).resolve().parent.parent

templates = Jinja2Templates(directory=str(BASE_PATH / "templates"))

router = APIRouter()


@router.get("/", status_code=status.HTTP_200_OK)
async def index(request: Request) -> HTMLResponse:
    """
    Render the index (home) page.

    Args:
        request (Request): The incoming HTTP request object.

    Returns:
        HTMLResponse: Rendered HTML response using the index.html Jinja2 template.
    """
    context = {"request": request}
    return templates.TemplateResponse("index.html", context=context)


@router.get("/api", status_code=status.HTTP_200_OK)
async def api_docs(request: Request) -> HTMLResponse:
    """
    Render the index (home) page.

    Args:
        request (Request): The incoming HTTP request object.

    Returns:
        HTMLResponse: Rendered HTML response using the index.html Jinja2 template.
    """
    context = {"request": request}
    return templates.TemplateResponse("api.html", context=context)


@router.get("/login", status_code=status.HTTP_200_OK)
async def login(request: Request) -> HTMLResponse:
    """
    Render the login page.

    Args:
        request (Request): The incoming HTTP request object.

    Returns:
        HTMLResponse: Rendered HTML response using the login.html Jinja2 template.
    """
    context = {"request": request}
    return templates.TemplateResponse("login.html", context=context)


@router.get("/dashboard", status_code=status.HTTP_200_OK, response_model=None)
async def dashboard(request: Request, is_logged: IsLoggedDep) -> HTMLResponse | RedirectResponse:
    """
    Render the dashboard page.

    Args:
        request (Request): The incoming HTTP request object.

    Returns:
        HTMLResponse: Rendered HTML response using the dashboard.html Jinja2 template.
    """
    if not is_logged:
        return RedirectResponse(request.url_for("login"), status_code=status.HTTP_302_FOUND)

    context = {"request": request}
    return templates.TemplateResponse("dashboard.html", context=context)


@router.get("/source", status_code=status.HTTP_200_OK, response_model=None)
async def source(request: Request, is_logged: IsLoggedDep) -> HTMLResponse | RedirectResponse:
    """
    Render the source management page if the user is logged in; otherwise, redirect to login.

    Args:
        request (Request): The incoming HTTP request.
        is_logged (IsLoggedDep): Dependency that indicates if the user is authenticated.

    Returns:
        HTMLResponse: Rendered 'source.html' template if logged in.
        RedirectResponse: Redirect to login page if not authenticated.
    """
    if not is_logged:
        return RedirectResponse(request.url_for("login"), status_code=status.HTTP_302_FOUND)

    context = {"request": request}
    return templates.TemplateResponse("source.html", context=context)
