from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.context import template_data
from app.database import get_db
from app.roles import STOK
from app.security import yetki_kontrol
from app.services.stok_service import hammaddeleri_listele, receteleri_listele, stok_tanimlari, stok_urunu_kaydet

router = APIRouter(tags=["Stok"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/urunler", response_class=HTMLResponse)
def urunler(request: Request, db: Session = Depends(get_db), yetki=Depends(yetki_kontrol(STOK))):
    data = template_data(request)
    data["urunler"] = hammaddeleri_listele(db)
    data["turler"], data["siniflar"] = stok_tanimlari(db)
    return templates.TemplateResponse("stok/urunler.html", data)


@router.post("/urunler")
def urun_kaydet(kodu: str = Form(""), adi: str = Form(""), stok_urun_turu_id: int = Form(...), stok_urun_sinifi_id: int | None = Form(None), birim: str = Form("Adet"), db: Session = Depends(get_db), yetki=Depends(yetki_kontrol(STOK))):
    try:
        stok_urunu_kaydet(db, kodu, adi, stok_urun_turu_id, stok_urun_sinifi_id, birim)
    except ValueError:
        return RedirectResponse("/urunler?error=1", status_code=303)
    return RedirectResponse("/urunler", status_code=303)


@router.get("/receteler", response_class=HTMLResponse)
def receteler(request: Request, db: Session = Depends(get_db), yetki=Depends(yetki_kontrol(STOK))):
    data = template_data(request)
    data["receteler"] = receteleri_listele(db)
    return templates.TemplateResponse("stok/receteler.html", data)
