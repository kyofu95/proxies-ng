from pathlib import Path

from fastapi import APIRouter, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

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


@router.get("/dashboard", status_code=status.HTTP_200_OK)
async def dashboard(request: Request) -> HTMLResponse:
    """
    Render the dashboard page.

    Args:
        request (Request): The incoming HTTP request object.

    Returns:
        HTMLResponse: Rendered HTML response using the dashboard.html Jinja2 template.
    """
    context = {"request": request}
    return templates.TemplateResponse("dashboard.html", context=context)
