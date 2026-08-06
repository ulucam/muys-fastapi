from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.context import template_data
from app.database import get_db
from app.roles import STOK
from app.security import yetki_kontrol
from app.services.stok_service import (
    hammaddeleri_listele,
    receteleri_listele,
    stok_sinifi_kaydet,
    stok_tanimlari,
    stok_turu_kaydet,
    stok_urunu_kaydet,
)

router = APIRouter(tags=["Stok"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/urunler", response_class=HTMLResponse)
def urunler(request: Request, error: str | None = None, db: Session = Depends(get_db), yetki=Depends(yetki_kontrol(STOK))):
    data = template_data(request)
    data["urunler"] = hammaddeleri_listele(db)
    data["turler"], data["siniflar"] = stok_tanimlari(db)
    data["hata"] = "Kayıt yapılamadı. Zorunlu alanları ve benzersiz ad/kod bilgisini kontrol edin." if error else None
    return templates.TemplateResponse("stok/urunler.html", data)


@router.post("/urunler")
def urun_kaydet(
    kodu: str = Form(""), adi: str = Form(""), stok_urun_turu_id: int = Form(...),
    stok_urun_sinifi_id: int | None = Form(None), birim: str = Form("Adet"),
    marka: str = Form(""), model: str = Form(""), mevcut_stok: float = Form(0),
    min_stok: float = Form(0), urun_id: int | None = Form(None),
    db: Session = Depends(get_db), yetki=Depends(yetki_kontrol(STOK)),
):
    try:
        stok_urunu_kaydet(db, kodu, adi, stok_urun_turu_id, stok_urun_sinifi_id, birim, marka, model, mevcut_stok, min_stok, urun_id)
    except ValueError:
        return RedirectResponse("/urunler?error=1", status_code=303)
    return RedirectResponse("/urunler", status_code=303)


@router.post("/urunler/tur/kaydet")
def tur_kaydet(adi: str = Form(""), tur_id: int | None = Form(None), db: Session = Depends(get_db), yetki=Depends(yetki_kontrol(STOK))):
    try:
        stok_turu_kaydet(db, adi, tur_id)
    except ValueError:
        return RedirectResponse("/urunler?error=tur", status_code=303)
    return RedirectResponse("/urunler", status_code=303)


@router.post("/urunler/sinif/kaydet")
def sinif_kaydet(adi: str = Form(""), sinif_id: int | None = Form(None), db: Session = Depends(get_db), yetki=Depends(yetki_kontrol(STOK))):
    try:
        stok_sinifi_kaydet(db, adi, sinif_id)
    except ValueError:
        return RedirectResponse("/urunler?error=sinif", status_code=303)
    return RedirectResponse("/urunler", status_code=303)


@router.get("/receteler", response_class=HTMLResponse)
def receteler(request: Request, db: Session = Depends(get_db), yetki=Depends(yetki_kontrol(STOK))):
    data = template_data(request)
    data["receteler"] = receteleri_listele(db)
    return templates.TemplateResponse("stok/receteler.html", data)
