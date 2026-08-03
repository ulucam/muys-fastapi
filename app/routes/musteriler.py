import io
import pandas as pd
from fastapi import APIRouter, Request, Depends, Form, File, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.musteri import Musteri
from app.context import template_data
from app.security import yetki_kontrol
from app.roles import MUSTERI
from app.roles import MUSTERI_YONET
from app.roles import ADMIN


router = APIRouter(
    prefix="/musteriler",
    tags=["Müşteriler"]
)

templates = Jinja2Templates(
    directory="app/templates"
)


# =====================================================
# MÜŞTERİ LİSTESİ
# =====================================================

@router.get("/", response_class=HTMLResponse)
def liste(
    request: Request,
    db: Session = Depends(get_db),
    yetki=Depends(yetki_kontrol(MUSTERI))
):
    musteriler = (
        db.query(Musteri)
        .order_by(Musteri.id.desc())
        .all()
    )

    data = template_data(request)
    data["musteriler"] = musteriler

    return templates.TemplateResponse(
        "musteri/index.html",
        data
    )


# =====================================================
# EXCEL İÇE AKTAR (EXCEL IMPORT)
# =====================================================

@router.post("/excel-import")
async def excel_import(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    yetki=Depends(yetki_kontrol(MUSTERI_YONET))
):
    if not file.filename.endswith((".xlsx", ".xls")):
        # Excel formatı dışında bir dosya yüklendiyse geri yönlendir
        return RedirectResponse("/musteriler?error=invalid_format", status_code=303)

    try:
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))

        # Kolon isimlerini standartlaştır (küçük harf, boşluksuz)
        df.columns = [str(col).strip().lower() for col in df.columns]

        for _, row in df.iterrows():
            firma_adi = str(row.get("firma_adi", "") or row.get("firma adı", "")).strip()
            
            # Firma adı boşsa bu satırı atla
            if not firma_adi or firma_adi.lower() == "nan":
                continue

            # Kod üretimi
            son = db.query(Musteri).order_by(Musteri.id.desc()).first()
            kod = f"M{son.id + 1:06}" if son else "M000001"

            musteri = Musteri(
                musteri_kodu=kod,
                firma_adi=firma_adi,
                yetkili="" if pd.isna(row.get("yetkili")) else str(row.get("yetkili")).strip(),
                telefon="" if pd.isna(row.get("telefon")) else str(row.get("telefon")).strip(),
                email="" if pd.isna(row.get("email")) else str(row.get("email")).strip(),
                vergi_dairesi="" if pd.isna(row.get("vergi_dairesi")) else str(row.get("vergi_dairesi")).strip(),
                vergi_no="" if pd.isna(row.get("vergi_no")) else str(row.get("vergi_no")).strip(),
                il="" if pd.isna(row.get("il")) else str(row.get("il")).strip(),
                ilce="" if pd.isna(row.get("ilce")) else str(row.get("ilce")).strip(),
                adres="" if pd.isna(row.get("adres")) else str(row.get("adres")).strip(),
                aciklama="" if pd.isna(row.get("aciklama")) else str(row.get("aciklama")).strip(),
                aktif=True
            )
            db.add(musteri)
            db.flush()  # id'nin sıradaki satır için otomatik güncellenmesini sağlar

        db.commit()
        return RedirectResponse("/musteriler?success=imported", status_code=303)

    except Exception as e:
        db.rollback()
        return RedirectResponse("/musteriler?error=import_failed", status_code=303)


# =====================================================
# MÜŞTERİ EKLE FORM
# =====================================================

@router.get("/ekle", response_class=HTMLResponse)
def ekle_form(
    request: Request,
    yetki=Depends(yetki_kontrol(MUSTERI))
):
    return templates.TemplateResponse(
        "musteri/ekle.html",
        template_data(request)
    )


# =====================================================
# MÜŞTERİ EKLE
# =====================================================

@router.post("/ekle")
def ekle(
    firma_adi: str = Form(...),
    yetkili: str = Form(""),
    telefon: str = Form(""),
    email: str = Form(""),
    vergi_dairesi: str = Form(""),
    vergi_no: str = Form(""),
    il: str = Form(""),
    ilce: str = Form(""),
    adres: str = Form(""),
    aciklama: str = Form(""),

    db: Session = Depends(get_db),

    yetki = Depends(
        yetki_kontrol(MUSTERI_YONET)
    )
):

    son = db.query(Musteri).order_by(
        Musteri.id.desc()
    ).first()

    if son:
        kod = f"M{son.id + 1:06}"
    else:
        kod = "M000001"

    musteri = Musteri(
        musteri_kodu=kod,
        firma_adi=firma_adi,
        yetkili=yetkili,
        telefon=telefon,
        email=email,
        vergi_dairesi=vergi_dairesi,
        vergi_no=vergi_no,
        il=il,
        ilce=ilce,
        adres=adres,
        aciklama=aciklama
    )

    db.add(musteri)
    db.commit()

    return RedirectResponse(
        "/musteriler",
        status_code=303
    )


# =====================================================
# MÜŞTERİ DÜZENLE FORM
# =====================================================

@router.get("/duzenle/{id}", response_class=HTMLResponse)
def duzenle_form(
    id: int,
    request: Request,
    db: Session = Depends(get_db),

    yetki = Depends(
        yetki_kontrol(MUSTERI_YONET)
    )
):

    musteri = (
        db.query(Musteri)
        .filter(Musteri.id == id)
        .first()
    )

    if not musteri:
        return RedirectResponse(
            "/musteriler",
            status_code=303
        )

    data = template_data(request)
    data["musteri"] = musteri

    return templates.TemplateResponse(
        "musteri/duzenle.html",
        data
    )


# =====================================================
# MÜŞTERİ DÜZENLE
# =====================================================

@router.post("/duzenle/{id}")
def duzenle(
    id: int,

    firma_adi: str = Form(...),
    yetkili: str = Form(""),
    telefon: str = Form(""),
    email: str = Form(""),
    vergi_dairesi: str = Form(""),
    vergi_no: str = Form(""),
    il: str = Form(""),
    ilce: str = Form(""),
    adres: str = Form(""),
    aktif: bool = Form(True),
    aciklama: str = Form(""),

    db: Session = Depends(get_db),

    yetki = Depends(
        yetki_kontrol(MUSTERI_YONET)
    )
):

    musteri = (
        db.query(Musteri)
        .filter(Musteri.id == id)
        .first()
    )

    if not musteri:
        return RedirectResponse(
            "/musteriler",
            status_code=303
        )

    musteri.firma_adi = firma_adi
    musteri.yetkili = yetkili
    musteri.telefon = telefon
    musteri.email = email
    musteri.vergi_dairesi = vergi_dairesi
    musteri.vergi_no = vergi_no
    musteri.il = il
    musteri.ilce = ilce
    musteri.adres = adres
    musteri.aktif = aktif
    musteri.aciklama = aciklama

    db.commit()

    return RedirectResponse(
        "/musteriler",
        status_code=303
    )


# =====================================================
# MÜŞTERİ DETAY
# =====================================================

@router.get("/detay/{id}", response_class=HTMLResponse)
def detay(
    id: int,
    request: Request,
    db: Session = Depends(get_db),

    yetki=Depends(yetki_kontrol(MUSTERI))
):

    musteri = (
        db.query(Musteri)
        .filter(Musteri.id == id)
        .first()
    )

    if not musteri:
        return RedirectResponse(
            "/musteriler",
            status_code=303
        )

    data = template_data(request)

    data.update({
        "musteri": musteri,

        # Sipariş modülü bağlanınca gerçek veriler gelecek
        "siparislar": [],
        "bekleyen_siparis": 0,
        "uretimdeki_siparis": 0,
        "tamamlanan_siparis": 0,
        "toplam_siparis": 0
    })

    return templates.TemplateResponse(
        "musteri/detay.html",
        data
    )


# =====================================================
# MÜŞTERİ SİL
# =====================================================

@router.get("/sil/{id}")
def sil(
    id: int,

    db: Session = Depends(get_db),

    yetki=Depends(yetki_kontrol(ADMIN))
):

    musteri = (
        db.query(Musteri)
        .filter(Musteri.id == id)
        .first()
    )

    if musteri:
        db.delete(musteri)
        db.commit()

    return RedirectResponse(
        "/musteriler",
        status_code=303
    )
