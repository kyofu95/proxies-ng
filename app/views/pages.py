from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

BASE_PATH = Path(__file__).resolve().parent.parent

templates = Jinja2Templates(directory=str(BASE_PATH / "templates"))

router = APIRouter()


@router.get("/", status_code=200)
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
