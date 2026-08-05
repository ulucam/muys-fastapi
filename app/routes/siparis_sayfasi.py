from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.context import template_data
from app.database import get_db
from app.roles import SIPARIS
from app.security import yetki_kontrol
from app.services.siparis_service import SIPARIS_DURUMLARI, siparis_sayfasi_verisi


router = APIRouter(tags=["Siparişler"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/siparisler", response_class=HTMLResponse)
def siparisler(
    request: Request,
    musteri_id: int | None = None,
    durum: str | None = None,
    db: Session = Depends(get_db),
    yetki=Depends(yetki_kontrol(SIPARIS)),
):
    musteri, siparisler_duruma_gore = siparis_sayfasi_verisi(db, musteri_id, durum)
    durumlar = list(SIPARIS_DURUMLARI)
    data = template_data(request)
    data.update({
        "musteri_id": musteri_id,
        "musteri": musteri,
        "durum": durum,
        "durumlar": durumlar,
        "siparisler_duruma_gore": siparisler_duruma_gore,
    })
    return templates.TemplateResponse("siparisler/index.html", data)
