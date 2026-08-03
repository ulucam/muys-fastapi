from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.context import template_data

router = APIRouter()

templates = Jinja2Templates(
    directory="app/templates"
)


@router.get("/ayarlar", response_class=HTMLResponse)
async def ayarlar(request: Request):

    return templates.TemplateResponse(
        "ayarlar/index.html",
        template_data(request)
    )


@router.get("/ayarlar/excel", response_class=HTMLResponse)
async def excel(request: Request):

    return templates.TemplateResponse(
        "ayarlar/excel.html",
        template_data(request)
    )


@router.get("/ayarlar/yedek", response_class=HTMLResponse)
async def yedek(request: Request):

    return templates.TemplateResponse(
        "ayarlar/yedek.html",
        template_data(request)
    )


@router.get("/ayarlar/loglar", response_class=HTMLResponse)
async def loglar(request: Request):

    return templates.TemplateResponse(
        "ayarlar/loglar.html",
        template_data(request)
    )


@router.get("/ayarlar/firma", response_class=HTMLResponse)
async def firma(request: Request):

    return templates.TemplateResponse(
        "ayarlar/firma.html",
        template_data(request)
    )


@router.get("/ayarlar/sistem", response_class=HTMLResponse)
async def sistem(request: Request):

    return templates.TemplateResponse(
        "ayarlar/sistem.html",
        template_data(request)
    )
