from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.context import template_data
from app.security import yetki_kontrol
from app.password import sifre_olustur
from app.roles import KULLANICI


router = APIRouter(
    prefix="/kullanicilar",
    tags=["Kullanıcılar"]
)


templates = Jinja2Templates(
    directory="app/templates"
)



# =====================================================
# KULLANICI LİSTE
# =====================================================

@router.get("/", response_class=HTMLResponse)
def liste(
    request: Request,
    db: Session = Depends(get_db),
    yetki=Depends(yetki_kontrol(KULLANICI))
):

    kullanicilar = (
        db.query(User)
        .filter(User.rol != "Admin")
        .order_by(User.id.desc())
        .all()
    )


    data = template_data(request)

    data.update({
        "kullanicilar": kullanicilar
    })


    return templates.TemplateResponse(
        "kullanici/index.html",
        data
    )



# =====================================================
# YENİ KULLANICI FORM
# =====================================================

@router.get("/ekle", response_class=HTMLResponse)
def ekle_form(
    request: Request,
    yetki=Depends(yetki_kontrol(KULLANICI))
):

    data = template_data(request)


    return templates.TemplateResponse(
        "kullanici/ekle.html",
        data
    )



# =====================================================
# YENİ KULLANICI KAYDET
# =====================================================

@router.post("/ekle")
def ekle(

    kullanici_adi: str = Form(...),
    sifre: str = Form(...),
    ad_soyad: str = Form(...),
    email: str = Form(""),
    telefon: str = Form(""),
    rol: str = Form(...),

    db: Session = Depends(get_db),

    yetki=Depends(yetki_kontrol(KULLANICI))

):


    mevcut = (
        db.query(User)
        .filter(
            User.kullanici_adi == kullanici_adi
        )
        .first()
    )


    if mevcut:

        return RedirectResponse(
            "/kullanicilar/ekle",
            status_code=303
        )



    yeni = User(

        kullanici_adi=kullanici_adi,

        sifre=sifre_olustur(sifre),

        ad_soyad=ad_soyad,

        email=email if email else None,

        telefon=telefon if telefon else None,

        rol=rol,

        aktif=True

    )


    db.add(yeni)

    db.commit()


    return RedirectResponse(
        "/kullanicilar",
        status_code=303
    )



# =====================================================
# DÜZENLE FORM
# =====================================================

@router.get("/duzenle/{id}", response_class=HTMLResponse)
def duzenle_form(

    id: int,

    request: Request,

    db: Session = Depends(get_db),

    yetki=Depends(yetki_kontrol(KULLANICI))

):


    kullanici = (
        db.query(User)
        .filter(User.id == id)
        .first()
    )


    if not kullanici or kullanici.rol == "Admin":

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
# DÜZENLE KAYDET
# =====================================================

@router.post("/duzenle/{id}")
def duzenle(

    id: int,

    kullanici_adi: str = Form(...),
    ad_soyad: str = Form(...),
    email: str = Form(""),
    telefon: str = Form(""),
    rol: str = Form(...),
    aktif: bool = Form(True),

    db: Session = Depends(get_db),

    yetki=Depends(yetki_kontrol(KULLANICI))

):


    kullanici = (
        db.query(User)
        .filter(User.id == id)
        .first()
    )


    if kullanici and kullanici.rol != "Admin":


        kullanici.kullanici_adi = kullanici_adi

        kullanici.ad_soyad = ad_soyad

        kullanici.email = email if email else None

        kullanici.telefon = telefon if telefon else None

        kullanici.rol = rol

        kullanici.aktif = aktif


        db.commit()



    return RedirectResponse(
        "/kullanicilar",
        status_code=303
    )



# =====================================================
# ŞİFRE FORM
# =====================================================

@router.get("/sifre/{id}", response_class=HTMLResponse)
def sifre_form(

    id: int,

    request: Request,

    db: Session = Depends(get_db),

    yetki=Depends(yetki_kontrol(KULLANICI))

):


    kullanici = (
        db.query(User)
        .filter(User.id == id)
        .first()
    )


    if not kullanici or kullanici.rol == "Admin":

        return RedirectResponse(
            "/kullanicilar",
            status_code=303
        )


    data = template_data(request)

    data["kullanici"] = kullanici


    return templates.TemplateResponse(
        "kullanici/sifre.html",
        data
    )



# =====================================================
# ŞİFRE DEĞİŞTİR
# =====================================================

@router.post("/sifre/{id}")
def sifre_degistir(

    id: int,

    sifre: str = Form(...),

    sifre_tekrar: str = Form(...),


    db: Session = Depends(get_db),

    yetki=Depends(yetki_kontrol(KULLANICI))

):


    if sifre != sifre_tekrar:

        return RedirectResponse(
            f"/kullanicilar/sifre/{id}",
            status_code=303
        )



    kullanici = (
        db.query(User)
        .filter(User.id == id)
        .first()
    )


    if kullanici and kullanici.rol != "Admin":


        kullanici.sifre = sifre_olustur(sifre)

        db.commit()



    return RedirectResponse(
        "/kullanicilar",
        status_code=303
    )



# =====================================================
# SİL
# =====================================================

@router.get("/sil/{id}")
def sil(

    id: int,

    db: Session = Depends(get_db),

    yetki=Depends(yetki_kontrol(KULLANICI))

):


    kullanici = (
        db.query(User)
        .filter(User.id == id)
        .first()
    )


    # Admin kesinlikle silinemez

    if kullanici and kullanici.rol != "Admin":

        db.delete(kullanici)

        db.commit()



    return RedirectResponse(
        "/kullanicilar",
        status_code=303
    )