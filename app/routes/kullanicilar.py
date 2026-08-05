from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.context import template_data
from app.database import get_db
from app.roles import ADMIN, YONETIM
from app.security import yetki_kontrol
from app.services.kullanici_service import (
    form_secenekleri,
    kullanici_getir,
    kullanici_guncelle,
    kullanici_olustur,
    kullanici_sil,
    kullanicilari_listele,
)

router = APIRouter(prefix="/kullanicilar", tags=["Kullanıcılar"])
templates = Jinja2Templates(directory="app/templates")


def kullanici_form_verisi(request: Request, db: Session, **ek):
    istasyonlar, personeller = form_secenekleri(db)
    data = template_data(request)
    data.update({"istasyonlar": istasyonlar, "personeller": personeller, **ek})
    return data


@router.get("/", response_class=HTMLResponse)
def liste(request: Request, filtre: str = "", db: Session = Depends(get_db), yetki=Depends(yetki_kontrol(YONETIM))):
    kullanicilar = kullanicilari_listele(db)
    istasyonlar, personeller = form_secenekleri(db, sadece_aktif=False)
    data = template_data(request)
    data.update({"kullanicilar": kullanicilar, "istasyonlar": istasyonlar, "personeller": personeller, "liste_basligi": None})
    if filtre == "toplam":
        data.update({"gosterilecek_kullanicilar": kullanicilar, "liste_basligi": "Tüm Kullanıcılar"})
    elif filtre == "aktif":
        data.update({"gosterilecek_kullanicilar": [k for k in kullanicilar if k.aktif], "liste_basligi": "Aktif Kullanıcılar"})
    return templates.TemplateResponse("kullanici/index.html", data)


@router.get("/ekle", response_class=HTMLResponse)
def ekle_form(request: Request, db: Session = Depends(get_db), yetki=Depends(yetki_kontrol(ADMIN))):
    return templates.TemplateResponse("kullanici/ekle.html", kullanici_form_verisi(request, db))


@router.post("/ekle")
def ekle(
    request: Request,
    kullanici_adi: str = Form(...), ad_soyad: str = Form(...), telefon: str = Form(""),
    email: str = Form(""), rol: str = Form(...), istasyon_id: int | None = Form(None),
    personel_id: int | None = Form(None), aktif: bool = Form(True), sifre: str = Form(...),
    db: Session = Depends(get_db), yetki=Depends(yetki_kontrol(ADMIN)),
):
    sonuc = kullanici_olustur(db, kullanici_adi=kullanici_adi, ad_soyad=ad_soyad, telefon=telefon,
        email=email, rol=rol, istasyon_id=istasyon_id, personel_id=personel_id, aktif=aktif, sifre=sifre)
    if sonuc.hata:
        return templates.TemplateResponse("kullanici/ekle.html", kullanici_form_verisi(request, db, hata=sonuc.hata), status_code=sonuc.durum_kodu)
    return RedirectResponse("/kullanicilar", status_code=303)


@router.get("/duzenle/{id}", response_class=HTMLResponse)
def duzenle_form(id: int, request: Request, db: Session = Depends(get_db), yetki=Depends(yetki_kontrol(YONETIM))):
    kullanici = kullanici_getir(db, id)
    if not kullanici:
        return RedirectResponse("/kullanicilar", status_code=303)
    return templates.TemplateResponse("kullanici/duzenle.html", kullanici_form_verisi(request, db, kullanici=kullanici))


@router.post("/duzenle/{id}")
def duzenle(
    id: int, request: Request,
    kullanici_adi: str = Form(...), ad_soyad: str = Form(""), telefon: str = Form(""),
    email: str = Form(""), rol: str = Form(...), istasyon_id: int | None = Form(None),
    personel_id: int | None = Form(None), aktif: bool = Form(True), sifre: str = Form(""),
    db: Session = Depends(get_db), yetki=Depends(yetki_kontrol(YONETIM)),
):
    sonuc = kullanici_guncelle(db, id, kullanici_adi=kullanici_adi, ad_soyad=ad_soyad, telefon=telefon,
        email=email, rol=rol, istasyon_id=istasyon_id, personel_id=personel_id, aktif=aktif, sifre=sifre)
    if not sonuc.kullanici:
        return RedirectResponse("/kullanicilar", status_code=303)
    if sonuc.hata:
        return templates.TemplateResponse("kullanici/duzenle.html", kullanici_form_verisi(request, db, hata=sonuc.hata, kullanici=sonuc.kullanici), status_code=sonuc.durum_kodu)
    return RedirectResponse("/kullanicilar", status_code=303)


@router.get("/sil/{id}")
def sil(id: int, db: Session = Depends(get_db), yetki=Depends(yetki_kontrol(ADMIN))):
    kullanici_sil(db, id)
    return RedirectResponse("/kullanicilar", status_code=303)
