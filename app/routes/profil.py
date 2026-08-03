from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.context import template_data

router = APIRouter()

templates = Jinja2Templates(
    directory="app/templates"
)


@router.get("/profil", response_class=HTMLResponse)
async def profil(request: Request):

    return templates.TemplateResponse(
        "profil/index.html",
        template_data(request)
    )
