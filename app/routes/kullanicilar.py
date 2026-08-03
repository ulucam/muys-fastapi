from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.context import template_data
from app.security import yetki_kontrol
from app.password import sifre_olustur
from app.roles import ADMIN

router = APIRouter(
    prefix="/kullanicilar",
    tags=["Kullanıcılar"]
)

templates = Jinja2Templates(directory="app/templates")


# =====================================================
# KULLANICI LİSTESİ
# =====================================================

@router.get("/", response_class=HTMLResponse)
def liste(
    request: Request,
    db: Session = Depends(get_db),
    yetki=Depends(yetki_kontrol(ADMIN))
):
    kullanicilar = (
        db.query(User)
        .order_by(User.id.desc())
        .all()
    )

    data = template_data(request)
    data["kullanicilar"] = kullanicilar

    return templates.TemplateResponse(
        "kullanici/index.html",
        data
    )


# =====================================================
# KULLANICI EKLE FORM (GET)
# =====================================================

@router.get("/ekle", response_class=HTMLResponse)
def ekle_form(
    request: Request,
    yetki=Depends(yetki_kontrol(ADMIN))
):
    return templates.TemplateResponse(
        "kullanici/ekle.html",
        template_data(request)
    )


# =====================================================
# KULLANICI EKLE (POST)
# =====================================================

@router.post("/ekle")
def ekle(
    request: Request,
    kullanici_adi: str = Form(...),
    ad_soyad: str = Form(...),
    telefon: str = Form(""),
    email: str = Form(""),
    rol: str = Form(...),
    aktif: bool = Form(True),
    sifre: str = Form(...),


    
    db: Session = Depends(get_db),
    yetki=Depends(yetki_kontrol(ADMIN))
):
    # Aynı kullanıcı adı var mı?
    var_mi = (
        db.query(User)
        .filter(User.kullanici_adi == kullanici_adi)
        .first()
    )

    if var_mi:
        data = template_data(request)
        data["hata"] = "Bu kullanıcı adı zaten kayıtlı."

        return templates.TemplateResponse(
            "kullanici/ekle.html",
            data
        )

    yeni_kullanici = User(
    kullanici_adi=kullanici_adi,
    ad_soyad=ad_soyad,
    telefon=telefon,
    email=email,
    rol=rol,
    aktif=aktif,
    sifre=sifre_olustur(sifre)
    )

    db.add(yeni_kullanici)
    db.commit()

    return RedirectResponse(
        "/kullanicilar",
        status_code=303
    )

# =====================================================
# KULLANICI DÜZENLE FORM (GET)
# =====================================================

@router.get("/duzenle/{id}", response_class=HTMLResponse)
def duzenle_form(
    id: int,
    request: Request,
    db: Session = Depends(get_db),
    yetki=Depends(yetki_kontrol(ADMIN))
):
    kullanici = (
        db.query(User)
        .filter(User.id == id)
        .first()
    )

    if not kullanici:
        return RedirectResponse(
            "/kullanicilar",
            status_code=303
        )

    data = template_data(request)
    data["kullanici"] = kullanici

    return templates.TemplateResponse(
        "kullanici/duzenle.html",
        data
    )


# =====================================================
# KULLANICI DÜZENLE (POST)
# =====================================================

@router.post("/duzenle/{id}")
def duzenle(
    id: int,
    kullanici_adi: str = Form(...),
    ad_soyad: str = Form(""),
    telefon: str = Form(""),
    email: str = Form(""),
    rol: str = Form(...),
    aktif: bool = Form(True),
    sifre: str = Form(""),  
    db: Session = Depends(get_db),
    yetki=Depends(yetki_kontrol(ADMIN))
):
    kullanici = (
        db.query(User)
        .filter(User.id == id)
        .first()
    )

    if not kullanici:
        return RedirectResponse(
            "/kullanicilar",
            status_code=303
        )

    kullanici.kullanici_adi = kullanici_adi
    kullanici.ad_soyad = ad_soyad
    kullanici.telefon = telefon
    kullanici.email = email
    kullanici.rol = rol
    kullanici.aktif = aktif

    if sifre.strip():
     kullanici.sifre = sifre_olustur(sifre)

    db.commit()

    return RedirectResponse(
        "/kullanicilar",
        status_code=303
    )


# =====================================================
# KULLANICI SİL
# =====================================================

@router.get("/sil/{id}")
def sil(
    id: int,
    db: Session = Depends(get_db),
    yetki=Depends(yetki_kontrol(ADMIN))
):
    kullanici = (
        db.query(User)
        .filter(User.id == id)
        .first()
    )

    if kullanici:
        db.delete(kullanici)
        db.commit()

    return RedirectResponse(
        "/kullanicilar",
        status_code=303
    )
