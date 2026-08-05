from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.context import template_data
from app.database import get_db
from app.models.musteri import Musteri
from app.models.siparis import Siparis
from app.roles import SIPARIS
from app.security import yetki_kontrol


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
    musteri = db.query(Musteri).filter(Musteri.id == musteri_id).first() if musteri_id else None
    siparis_sorgusu = db.query(Siparis)
    if musteri_id:
        siparis_sorgusu = siparis_sorgusu.filter(Siparis.musteri_id == musteri_id)
    if durum:
        siparis_sorgusu = siparis_sorgusu.filter(Siparis.durum == durum)
    siparisler = siparis_sorgusu.order_by(Siparis.teslim_tarihi.asc(), Siparis.created_at.desc()).all()
    durumlar = ["Beklemede", "Üretimde", "Sevke Hazır"]
    data = template_data(request)
    data.update({
        "musteri_id": musteri_id,
        "musteri": musteri,
        "durum": durum,
        "durumlar": durumlar,
        "siparisler_duruma_gore": {
            durum_adi: [siparis for siparis in siparisler if siparis.durum == durum_adi]
            for durum_adi in durumlar
        },
    })
    return templates.TemplateResponse("siparisler/index.html", data)
