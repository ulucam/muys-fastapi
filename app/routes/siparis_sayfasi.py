from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.context import template_data
from app.roles import MUSTERI
from app.security import yetki_kontrol


router = APIRouter(tags=["Siparişler"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/siparisler", response_class=HTMLResponse)
def siparisler(
    request: Request,
    musteri_id: int | None = None,
    durum: str | None = None,
    yetki=Depends(yetki_kontrol(MUSTERI)),
):
    data = template_data(request)
    data.update({"musteri_id": musteri_id, "durum": durum})
    return templates.TemplateResponse("siparisler/index.html", data)
