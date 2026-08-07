from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.context import template_data
from app.database import get_db
from app.models.rol_sinifi import RolSinifi
from app.roles import ADMIN
from app.security import kullanici_yonetim_kontrol, yetki_kontrol
from app.services.islem_log_service import islem_logla
from app.services.kullanici_service import (atanabilir_personeller, form_secenekleri, kullanici_getir,
    kullanici_guncelle, kullanici_olustur, kullanici_sil, kullanicilari_listele, personel_istasyon_secenekleri,
    rol_secenekleri)

router = APIRouter(prefix="/kullanicilar", tags=["Kullanıcılar"])
templates = Jinja2Templates(directory="app/templates")


def _form_verisi(request, db, kullanici=None, **ek):
    istasyonlar, _ = form_secenekleri(db)
    data = template_data(request)
    data.update({"istasyonlar": istasyonlar, "personeller": atanabilir_personeller(db, kullanici.id if kullanici else None),
        "personel_istasyonlari": personel_istasyon_secenekleri(db), "roller": rol_secenekleri(db, request.session.get("rol", "")),
        "kullanici": kullanici, **ek})
    return data


@router.get("/", response_class=HTMLResponse)
def liste(request: Request, db: Session = Depends(get_db), yetki=Depends(kullanici_yonetim_kontrol)):
    data = template_data(request)
    data.update({"kullanicilar": kullanicilari_listele(db), "roller": db.query(RolSinifi).order_by(RolSinifi.seviye.desc()).all()})
    return templates.TemplateResponse("kullanici/index.html", data)


@router.get("/ekle", response_class=HTMLResponse)
def ekle_form(request: Request, db: Session = Depends(get_db), yetki=Depends(kullanici_yonetim_kontrol)):
    return templates.TemplateResponse("kullanici/ekle.html", _form_verisi(request, db))


@router.post("/ekle")
def ekle(request: Request, kullanici_adi: str = Form(...), sifre: str = Form(...), personel_id: int = Form(...),
    telefon: str = Form(""), email: str = Form(""), rol: str = Form(...), aktif: bool = Form(True),
    db: Session = Depends(get_db), yetki=Depends(kullanici_yonetim_kontrol)):
    sonuc = kullanici_olustur(db, request.session.get("rol", ""), kullanici_adi=kullanici_adi, sifre=sifre,
        personel_id=personel_id, telefon=telefon, email=email, rol=rol, aktif=aktif)
    if sonuc.hata:
        return templates.TemplateResponse("kullanici/ekle.html", _form_verisi(request, db, hata=sonuc.hata), status_code=sonuc.durum_kodu)
    islem_logla(db, request, "Kullanıcılar", "Kullanıcı oluşturuldu", f"{kullanici_adi} · {rol}", commit=True)
    return RedirectResponse("/kullanicilar#module-kullanicilar", status_code=303)


@router.get("/duzenle/{id}", response_class=HTMLResponse)
def duzenle_form(id: int, request: Request, db: Session = Depends(get_db), yetki=Depends(kullanici_yonetim_kontrol)):
    kullanici = kullanici_getir(db, id)
    if not kullanici:
        return RedirectResponse("/kullanicilar", status_code=303)
    return templates.TemplateResponse("kullanici/duzenle.html", _form_verisi(request, db, kullanici))


@router.post("/duzenle/{id}")
def duzenle(id: int, request: Request, kullanici_adi: str = Form(...), sifre: str = Form(""), personel_id: int = Form(...),
    telefon: str = Form(""), email: str = Form(""), rol: str = Form(...), aktif: bool = Form(True),
    db: Session = Depends(get_db), yetki=Depends(kullanici_yonetim_kontrol)):
    sonuc = kullanici_guncelle(db, id, request.session.get("rol", ""), kullanici_adi=kullanici_adi, sifre=sifre,
        personel_id=personel_id, telefon=telefon, email=email, rol=rol, aktif=aktif)
    if not sonuc.kullanici:
        return RedirectResponse("/kullanicilar", status_code=303)
    if sonuc.hata:
        return templates.TemplateResponse("kullanici/duzenle.html", _form_verisi(request, db, sonuc.kullanici, hata=sonuc.hata), status_code=sonuc.durum_kodu)
    islem_logla(db, request, "Kullanıcılar", "Kullanıcı güncellendi", kullanici_adi, commit=True)
    return RedirectResponse("/kullanicilar", status_code=303)


@router.post("/roller")
def rol_kaydet(request: Request, adi: str = Form(...), seviye: int = Form(...), kullanici_ekleyebilir: bool = Form(False),
    yetkiler: str = Form(""), aciklama: str = Form(""), rol_id: int | None = Form(None), db: Session = Depends(get_db),
    yetki=Depends(yetki_kontrol(ADMIN))):
    rol = db.query(RolSinifi).filter(RolSinifi.id == rol_id).first() if rol_id else RolSinifi()
    if rol_id and not rol:
        raise HTTPException(404, "Rol bulunamadı.")
    if rol and rol.adi == "Admin":
        raise HTTPException(400, "Admin rolü değiştirilemez.")
    adi = adi.strip()
    if not adi or not 1 <= seviye < 100:
        raise HTTPException(400, "Rol seviyesi 1-99 arasında olmalıdır.")
    eski_ad = rol.adi if rol_id else None
    rol.adi, rol.seviye, rol.kullanici_ekleyebilir = adi, seviye, kullanici_ekleyebilir
    rol.yetkiler, rol.aciklama, rol.aktif = yetkiler.strip(), aciklama.strip(), True
    try:
        db.add(rol)
        if eski_ad and eski_ad != adi:
            from app.models.user import User
            db.query(User).filter(User.rol == eski_ad).update({User.rol: adi}, synchronize_session=False)
        db.commit()
    except IntegrityError:
        db.rollback(); raise HTTPException(400, "Bu rol adı zaten kullanılıyor.")
    islem_logla(db, request, "Kullanıcılar", "Rol sınıfı kaydedildi", f"{adi} · seviye {seviye}", commit=True)
    return RedirectResponse("/kullanicilar#module-roller", status_code=303)


@router.post("/sil/{id}")
def sil(id: int, request: Request, db: Session = Depends(get_db), yetki=Depends(yetki_kontrol(ADMIN))):
    kullanici_sil(db, id); islem_logla(db, request, "Kullanıcılar", "Kullanıcı silindi", str(id), commit=True)
    return RedirectResponse("/kullanicilar", status_code=303)
