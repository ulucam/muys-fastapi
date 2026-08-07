from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from app.templating import templates

from app.context import template_data

router = APIRouter()



@router.get("/profil", response_class=HTMLResponse)
async def profil(request: Request):

    return templates.TemplateResponse(
        "profil/index.html",
        template_data(request)
    )
