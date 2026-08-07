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
    stok_sinifi_sil,
    stok_tanim_kullanimlari,
    stok_kurulum_durumu,
    stok_tanimlari,
    stok_tum_tanimlari,
    stok_turu_kaydet,
    stok_turu_sil,
    stok_urunu_kaydet,
    stok_urunlerini_listele,
)

router = APIRouter(tags=["Stok"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/urunler", response_class=HTMLResponse)
def urunler(request: Request, error: str | None = None, db: Session = Depends(get_db), yetki=Depends(yetki_kontrol(STOK))):
    data = template_data(request)
    data["urunler"] = stok_urunlerini_listele(db)
    data["turler"], data["siniflar"] = stok_tum_tanimlari(db)
    return templates.TemplateResponse("stok/urun_listesi.html", data)


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
        return RedirectResponse("/receteler?error=urun#module-yeni-kart", status_code=303)
    return RedirectResponse("/receteler#module-stoklar", status_code=303)


@router.post("/urunler/tur/kaydet")
def tur_kaydet(adi: str = Form(""), db: Session = Depends(get_db), yetki=Depends(yetki_kontrol(STOK))):
    try:
        stok_turu_kaydet(db, adi)
    except ValueError:
        return RedirectResponse("/receteler?error=tur#module-tanimlar", status_code=303)
    return RedirectResponse("/receteler#module-tanimlar", status_code=303)


@router.post("/urunler/tur/{tur_id}/guncelle")
def tur_guncelle(tur_id: int, adi: str = Form(""), db: Session = Depends(get_db), yetki=Depends(yetki_kontrol(STOK))):
    try:
        stok_turu_kaydet(db, adi, tur_id)
    except ValueError:
        return RedirectResponse("/receteler?error=tur#module-tanimlar", status_code=303)
    return RedirectResponse("/receteler#module-tanimlar", status_code=303)


@router.post("/urunler/tur/{tur_id}/sil")
def tur_sil(tur_id: int, urunlerden_kaldir: bool = Form(False), db: Session = Depends(get_db), yetki=Depends(yetki_kontrol(STOK))):
    try:
        stok_turu_sil(db, tur_id, urunlerden_kaldir)
    except ValueError:
        return RedirectResponse("/receteler?error=tur_kullanim#module-tanimlar", status_code=303)
    return RedirectResponse("/receteler#module-tanimlar", status_code=303)


@router.post("/urunler/sinif/kaydet")
def sinif_kaydet(adi: str = Form(""), db: Session = Depends(get_db), yetki=Depends(yetki_kontrol(STOK))):
    try:
        stok_sinifi_kaydet(db, adi)
    except ValueError:
        return RedirectResponse("/receteler?error=sinif#module-tanimlar", status_code=303)
    return RedirectResponse("/receteler#module-tanimlar", status_code=303)


@router.post("/urunler/sinif/{sinif_id}/guncelle")
def sinif_guncelle(sinif_id: int, adi: str = Form(""), db: Session = Depends(get_db), yetki=Depends(yetki_kontrol(STOK))):
    try:
        stok_sinifi_kaydet(db, adi, sinif_id)
    except ValueError:
        return RedirectResponse("/receteler?error=sinif#module-tanimlar", status_code=303)
    return RedirectResponse("/receteler#module-tanimlar", status_code=303)


@router.post("/urunler/sinif/{sinif_id}/sil")
def sinif_sil(sinif_id: int, urunlerden_kaldir: bool = Form(False), db: Session = Depends(get_db), yetki=Depends(yetki_kontrol(STOK))):
    try:
        stok_sinifi_sil(db, sinif_id, urunlerden_kaldir)
    except ValueError:
        return RedirectResponse("/receteler?error=sinif_kullanim#module-tanimlar", status_code=303)
    return RedirectResponse("/receteler#module-tanimlar", status_code=303)


@router.get("/receteler", response_class=HTMLResponse)
def receteler(request: Request, error: str | None = None, db: Session = Depends(get_db), yetki=Depends(yetki_kontrol(STOK))):
    data = template_data(request)
    data["receteler"] = receteleri_listele(db)
    data["urunler"] = hammaddeleri_listele(db)
    data["turler"], data["siniflar"] = stok_tanimlari(db)
    data["kurulum"] = stok_kurulum_durumu(db)
    data["tanim_kullanimlari"] = stok_tanim_kullanimlari(db)
    kullanim_hatasi = error in ("tur_kullanim", "sinif_kullanim")
    data["hata"] = ("Tanım ürünlerde kullanılıyor. Ürünlerden kaldırıp sil seçeneğini kullanın." if kullanim_hatasi else "Kayıt yapılamadı. Zorunlu alanları ve benzersiz ad/kod bilgisini kontrol edin.") if error else None
    return templates.TemplateResponse("stok/urunler.html", data)
