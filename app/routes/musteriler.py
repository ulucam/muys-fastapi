import json
from pathlib import Path
from fastapi import APIRouter, Request, Depends, Form, File, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.context import template_data
from app.security import yetki_kontrol
from app.roles import MUSTERI
from app.roles import MUSTERI_YONET
from app.roles import ADMIN
from app.services.musteri_service import (
    musteri_detayi,
    musteri_getir,
    musteri_guncelle,
    musteri_olustur,
    musteri_sil,
    musterileri_excelden_aktar,
    musterileri_listele,
)


router = APIRouter(
    prefix="/musteriler",
    tags=["Müşteriler"]
)

templates = Jinja2Templates(
    directory="app/templates"
)

ILLER_DOSYASI = Path(__file__).resolve().parent.parent / "data" / "iller.js"

IL_BOLGELERI = {
    "Adana": "Akdeniz", "Adıyaman": "Güneydoğu Anadolu", "Afyonkarahisar": "Ege", "Ağrı": "Doğu Anadolu",
    "Aksaray": "İç Anadolu", "Amasya": "Karadeniz", "Ankara": "İç Anadolu", "Antalya": "Akdeniz",
    "Ardahan": "Doğu Anadolu", "Artvin": "Karadeniz", "Aydın": "Ege", "Balıkesir": "Marmara",
    "Bartın": "Karadeniz", "Batman": "Güneydoğu Anadolu", "Bayburt": "Karadeniz", "Bilecik": "Marmara",
    "Bingöl": "Doğu Anadolu", "Bitlis": "Doğu Anadolu", "Bolu": "Karadeniz", "Burdur": "Akdeniz",
    "Bursa": "Marmara", "Çanakkale": "Marmara", "Çankırı": "İç Anadolu", "Çorum": "Karadeniz",
    "Denizli": "Ege", "Diyarbakır": "Güneydoğu Anadolu", "Düzce": "Karadeniz", "Edirne": "Marmara",
    "Elazığ": "Doğu Anadolu", "Erzincan": "Doğu Anadolu", "Erzurum": "Doğu Anadolu", "Eskişehir": "İç Anadolu",
    "Gaziantep": "Güneydoğu Anadolu", "Giresun": "Karadeniz", "Gümüşhane": "Karadeniz", "Hakkari": "Doğu Anadolu",
    "Hatay": "Akdeniz", "Iğdır": "Doğu Anadolu", "Isparta": "Akdeniz", "İstanbul": "Marmara",
    "İzmir": "Ege", "Kahramanmaraş": "Akdeniz", "Karabük": "Karadeniz", "Karaman": "İç Anadolu",
    "Kars": "Doğu Anadolu", "Kastamonu": "Karadeniz", "Kayseri": "İç Anadolu", "Kırıkkale": "İç Anadolu",
    "Kırklareli": "Marmara", "Kırşehir": "İç Anadolu", "Kilis": "Güneydoğu Anadolu", "Kocaeli": "Marmara",
    "Konya": "İç Anadolu", "Kütahya": "Ege", "Malatya": "Doğu Anadolu", "Manisa": "Ege",
    "Mardin": "Güneydoğu Anadolu", "Mersin": "Akdeniz", "Muğla": "Ege", "Muş": "Doğu Anadolu",
    "Nevşehir": "İç Anadolu", "Niğde": "İç Anadolu", "Ordu": "Karadeniz", "Osmaniye": "Akdeniz",
    "Rize": "Karadeniz", "Sakarya": "Marmara", "Samsun": "Karadeniz", "Şanlıurfa": "Güneydoğu Anadolu",
    "Siirt": "Güneydoğu Anadolu", "Sinop": "Karadeniz", "Sivas": "İç Anadolu", "Şırnak": "Güneydoğu Anadolu",
    "Tekirdağ": "Marmara", "Tokat": "Karadeniz", "Trabzon": "Karadeniz", "Tunceli": "Doğu Anadolu",
    "Uşak": "Ege", "Van": "Doğu Anadolu", "Yalova": "Marmara", "Yozgat": "İç Anadolu", "Zonguldak": "Karadeniz",
}


def il_ilce_listesi():
    with ILLER_DOSYASI.open(encoding="utf-8") as dosya:
        return json.load(dosya)


# =====================================================
# MÜŞTERİ LİSTESİ
# =====================================================

@router.get("/", response_class=HTMLResponse)
def liste(
    request: Request,
    db: Session = Depends(get_db),
    yetki=Depends(yetki_kontrol(MUSTERI))
):
    # Pasif müşteriler ana listeden ayrılarak alt tablodan görüntülenir.
    musteriler, pasif_musteriler = musterileri_listele(db)

    data = template_data(request)
    data["musteriler"] = musteriler
    data["pasif_musteriler"] = pasif_musteriler
    tum_musteriler = musteriler + pasif_musteriler
    data["firma_adlari"] = sorted({musteri.firma_adi for musteri in tum_musteriler})
    data["iller"] = sorted({musteri.il for musteri in tum_musteriler if musteri.il})
    data["il_bolgeleri"] = IL_BOLGELERI
    data["bolgeler"] = sorted({IL_BOLGELERI.get(musteri.il, "Diğer") for musteri in tum_musteriler})

    return templates.TemplateResponse(
        "musteri/index.html",
        data
    )


# =====================================================
# EXCEL İÇE AKTAR (EXCEL IMPORT - PANDAS'SIZ / OPENPYXL)
# =====================================================

@router.post("/excel-import")
async def excel_import(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    yetki=Depends(yetki_kontrol(MUSTERI_YONET))
):
    if not file.filename.endswith((".xlsx", ".xls")):
        return RedirectResponse("/musteriler?error=invalid_format", status_code=303)

    try:
        musterileri_excelden_aktar(db, await file.read())
        return RedirectResponse("/musteriler?success=imported", status_code=303)

    except Exception:
        return RedirectResponse("/musteriler?error=import_failed", status_code=303)


# =====================================================
# MÜŞTERİ EKLE FORM
# =====================================================

@router.get("/ekle", response_class=HTMLResponse)
def ekle_form(
    request: Request,
    yetki=Depends(yetki_kontrol(MUSTERI))
):
    data = template_data(request)
    data["ilceler"] = il_ilce_listesi()

    return templates.TemplateResponse("musteri/ekle.html", data)


# =====================================================
# MÜŞTERİ EKLE
# =====================================================

@router.post("/ekle")
def ekle(
    firma_adi: str = Form(...),
    yetkili: str = Form(""),
    musteri_turu: str = Form("Alıcı"),
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

    musteri_olustur(
        db,
        firma_adi=firma_adi,
        musteri_turu=musteri_turu,
        yetkili=yetkili,
        telefon=telefon,
        email=email,
        vergi_dairesi=vergi_dairesi,
        vergi_no=vergi_no,
        il=il,
        ilce=ilce,
        adres=adres,
        aciklama=aciklama,
    )

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

    musteri = musteri_getir(db, id)

    if not musteri:
        return RedirectResponse(
            "/musteriler",
            status_code=303
        )

    data = template_data(request)
    data["musteri"] = musteri
    data["ilceler"] = il_ilce_listesi()

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
    musteri_turu: str = Form("Alıcı"),
    telefon: str = Form(""),
    email: str = Form(""),
    vergi_dairesi: str = Form(""),
    vergi_no: str = Form(""),
    il: str = Form(""),
    ilce: str = Form(""),
    adres: str = Form(""),
    aktif: str | None = Form(None),
    aciklama: str = Form(""),

    db: Session = Depends(get_db),

    yetki = Depends(
        yetki_kontrol(MUSTERI_YONET)
    )
):

    if not musteri_guncelle(
        db,
        id,
        firma_adi=firma_adi,
        musteri_turu=musteri_turu,
        yetkili=yetkili,
        telefon=telefon,
        email=email,
        vergi_dairesi=vergi_dairesi,
        vergi_no=vergi_no,
        il=il,
        ilce=ilce,
        adres=adres,
        aktif=aktif == "true",
        aciklama=aciklama,
    ):
        return RedirectResponse(
            "/musteriler",
            status_code=303
        )

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

    musteri, siparis_ozeti = musteri_detayi(db, id)

    if not musteri:
        return RedirectResponse(
            "/musteriler",
            status_code=303
        )

    data = template_data(request)
    data.update({"musteri": musteri, **siparis_ozeti})

    return templates.TemplateResponse(
        "musteri/detay.html",
        data
    )


# =====================================================
# MÜŞTERİ SİL
# =====================================================

@router.post("/sil/{id}")
def sil(
    id: int,

    db: Session = Depends(get_db),

    yetki=Depends(yetki_kontrol(ADMIN))
):

    if not musteri_sil(db, id):
        return RedirectResponse("/musteriler?error=silinemedi", status_code=303)

    return RedirectResponse(
        "/musteriler",
        status_code=303
    )
