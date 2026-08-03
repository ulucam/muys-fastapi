from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.context import template_data
from app.security import yetki_kontrol, get_password_hash
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
    yetki=Depends(yetki_kontrol(ADMIN))  # Sadece ADMIN
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
    yetki=Depends(yetki_kontrol(ADMIN))  # Sadece ADMIN
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
    username: str = Form(...),
    full_name: str = Form(""),
    email: str = Form(""),
    role: str = Form(...),
    sifre: str = Form(...),
    is_active: bool = Form(True),
    db: Session = Depends(get_db),
    yetki=Depends(yetki_kontrol(ADMIN))  # Sadece ADMIN
):
    yeni_kullanici = User(
        username=username,
        full_name=full_name,
        email=email,
        role=role,
        is_active=is_active,
        hashed_password=get_password_hash(sifre)
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
    yetki=Depends(yetki_kontrol(ADMIN))  # Sadece ADMIN
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
    username: str = Form(...),
    full_name: str = Form(""),
    email: str = Form(""),
    role: str = Form(...),
    is_active: bool = Form(True),
    sifre: str = Form(""),  # Şifre boş bırakılırsa güncellenmez
    db: Session = Depends(get_db),
    yetki=Depends(yetki_kontrol(ADMIN))  # Sadece ADMIN
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

    # Temel bilgileri güncelle
    kullanici.username = username
    kullanici.full_name = full_name
    kullanici.email = email
    kullanici.role = role
    kullanici.is_active = is_active

    # Eğer formdan yeni bir şifre geldiyse hash'le ve güncelle
    if sifre and sifre.strip():
        kullanici.hashed_password = get_password_hash(sifre)

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
    yetki=Depends(yetki_kontrol(ADMIN))  # Sadece ADMIN
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
