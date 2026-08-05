from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.istasyon import Istasyon
from app.models.personel import Personel
from app.context import template_data
from app.security import yetki_kontrol
from app.password import sifre_olustur
from app.roles import ADMIN, YONETIM

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
    filtre: str = "",
    db: Session = Depends(get_db),
    yetki=Depends(yetki_kontrol(YONETIM))
):
    kullanicilar = (
        db.query(User)
        .filter(func.lower(User.kullanici_adi) != "admin")
        .order_by(User.id.desc())
        .all()
    )

    data = template_data(request)
    data["kullanicilar"] = kullanicilar
    data["istasyonlar"] = db.query(Istasyon).order_by(Istasyon.kodu).all()
    data["personeller"] = db.query(Personel).order_by(Personel.ad_soyad).all()
    data["liste_basligi"] = None

    if filtre == "toplam":
        data["gosterilecek_kullanicilar"] = kullanicilar
        data["liste_basligi"] = "Tüm Kullanıcılar"
    elif filtre == "aktif":
        data["gosterilecek_kullanicilar"] = [
            kullanici for kullanici in kullanicilar if kullanici.aktif
        ]
        data["liste_basligi"] = "Aktif Kullanıcılar"

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
    db: Session = Depends(get_db),
    yetki=Depends(yetki_kontrol(ADMIN))
):
    return templates.TemplateResponse(
        "kullanici/ekle.html",
        {**template_data(request), "istasyonlar": db.query(Istasyon).filter(Istasyon.aktif.is_(True)).order_by(Istasyon.kodu).all(), "personeller": db.query(Personel).filter(Personel.aktif.is_(True)).order_by(Personel.ad_soyad).all()}
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
    istasyon_id: int | None = Form(None),
    personel_id: int | None = Form(None),
    aktif: bool = Form(True),
    sifre: str = Form(...),


    
    db: Session = Depends(get_db),
    yetki=Depends(yetki_kontrol(ADMIN))
):
    istasyon = db.query(Istasyon).filter(Istasyon.id == istasyon_id, Istasyon.aktif.is_(True)).first() if istasyon_id else None
    personel = db.query(Personel).filter(Personel.id == personel_id, Personel.aktif.is_(True)).first() if personel_id else None
    personel_kullanimda = db.query(User).filter(User.personel_id == personel_id).first() if personel_id else None
    if rol == "Operatör" and (not istasyon or not personel or personel_kullanimda):
        data = template_data(request)
        data.update({"hata": "Operatör için aktif istasyon ve başka hesaba atanmamış aktif personel seçilmelidir.", "istasyonlar": db.query(Istasyon).filter(Istasyon.aktif.is_(True)).order_by(Istasyon.kodu).all(), "personeller": db.query(Personel).filter(Personel.aktif.is_(True)).order_by(Personel.ad_soyad).all()})
        return templates.TemplateResponse("kullanici/ekle.html", data, status_code=400)
    # Aynı kullanıcı adı var mı?
    var_mi = (
        db.query(User)
        .filter(User.kullanici_adi == kullanici_adi)
        .first()
    )

    if var_mi:
        data = template_data(request)
        data["hata"] = "Bu kullanıcı adı zaten kayıtlı."
        data["istasyonlar"] = db.query(Istasyon).filter(Istasyon.aktif.is_(True)).order_by(Istasyon.kodu).all()
        data["personeller"] = db.query(Personel).filter(Personel.aktif.is_(True)).order_by(Personel.ad_soyad).all()

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
    istasyon_id=istasyon.id if rol == "Operatör" else None,
    personel_id=personel.id if rol == "Operatör" else None,
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
    yetki=Depends(yetki_kontrol(YONETIM))
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
    data["istasyonlar"] = db.query(Istasyon).filter(Istasyon.aktif.is_(True)).order_by(Istasyon.kodu).all()
    data["personeller"] = db.query(Personel).filter(Personel.aktif.is_(True)).order_by(Personel.ad_soyad).all()

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
    request: Request,
    kullanici_adi: str = Form(...),
    ad_soyad: str = Form(""),
    telefon: str = Form(""),
    email: str = Form(""),
    rol: str = Form(...),
    istasyon_id: int | None = Form(None),
    personel_id: int | None = Form(None),
    aktif: bool = Form(True),
    sifre: str = Form(""),  
    db: Session = Depends(get_db),
    yetki=Depends(yetki_kontrol(YONETIM))
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

    istasyon = db.query(Istasyon).filter(Istasyon.id == istasyon_id, Istasyon.aktif.is_(True)).first() if istasyon_id else None
    personel = db.query(Personel).filter(Personel.id == personel_id, Personel.aktif.is_(True)).first() if personel_id else None
    personel_kullanimda = db.query(User).filter(User.personel_id == personel_id, User.id != id).first() if personel_id else None
    if rol == "Operatör" and (not istasyon or not personel or personel_kullanimda):
        data = template_data(request)
        data.update({"hata": "Operatör için aktif istasyon ve başka hesaba atanmamış aktif personel seçilmelidir.", "kullanici": kullanici, "istasyonlar": db.query(Istasyon).filter(Istasyon.aktif.is_(True)).order_by(Istasyon.kodu).all(), "personeller": db.query(Personel).filter(Personel.aktif.is_(True)).order_by(Personel.ad_soyad).all()})
        return templates.TemplateResponse("kullanici/duzenle.html", data, status_code=400)

    kullanici.kullanici_adi = kullanici_adi
    kullanici.ad_soyad = ad_soyad
    kullanici.telefon = telefon
    kullanici.email = email
    kullanici.rol = rol
    kullanici.istasyon_id = istasyon.id if rol == "Operatör" else None
    kullanici.personel_id = personel.id if rol == "Operatör" else None
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
