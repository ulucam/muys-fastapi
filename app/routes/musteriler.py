import io
import json
import openpyxl
from pathlib import Path
from fastapi import APIRouter, Request, Depends, Form, File, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database import get_db
from app.models.musteri import Musteri
from app.models.siparis import Siparis
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
    musteriler = (
        db.query(Musteri)
        .filter(Musteri.aktif.is_(True))
        .order_by(Musteri.firma_adi.asc())
        .all()
    )
    pasif_musteriler = (
        db.query(Musteri)
        .filter(Musteri.aktif.is_(False))
        .order_by(Musteri.firma_adi.asc())
        .all()
    )

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
        contents = await file.read()
        workbook = openpyxl.load_workbook(filename=io.BytesIO(contents), data_only=True)
        sheet = workbook.active

        # İlk satırdaki başlıkları oku ve normalize et
        headers = []
        for cell in sheet[1]:
            val = str(cell.value or "").strip().lower().replace(" ", "_")
            headers.append(val)

        # Satırları dön (2. satırdan itibaren)
        for row in sheet.iter_rows(min_row=2, values_only=True):
            if not any(row):  # Tamamen boş satırsa atla
                continue

            row_data = dict(zip(headers, row))

            # Firma adı kontrolü
            firma_adi = str(row_data.get("firma_adi") or row_data.get("firma_adı") or "").strip()
            if not firma_adi or firma_adi.lower() == "none":
                continue

            # Kod üretimi
            son = db.query(Musteri).order_by(Musteri.id.desc()).first()
            kod = f"M{son.id + 1:06}" if son else "M000001"

            def clean_val(key):
                val = row_data.get(key)
                if val is None or str(val).lower() == "none":
                    return ""
                return str(val).strip()

            musteri = Musteri(
                musteri_kodu=kod,
                firma_adi=firma_adi,
                yetkili=clean_val("yetkili"),
                telefon=clean_val("telefon"),
                email=clean_val("email"),
                vergi_dairesi=clean_val("vergi_dairesi"),
                vergi_no=clean_val("vergi_no"),
                il=clean_val("il"),
                ilce=clean_val("ilce"),
                adres=clean_val("adres"),
                aciklama=clean_val("aciklama"),
                aktif=True
            )
            db.add(musteri)
            db.flush()

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
        musteri_turu=musteri_turu,
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
    musteri.musteri_turu = musteri_turu
    musteri.yetkili = yetkili
    musteri.telefon = telefon
    musteri.email = email
    musteri.vergi_dairesi = vergi_dairesi
    musteri.vergi_no = vergi_no
    musteri.il = il
    musteri.ilce = ilce
    musteri.adres = adres
    # İşaretlenmeyen checkbox form verisine hiç eklenmez; Form(True) kullanımı
    # müşteriyi tekrar aktif yapıyordu. Böylece işaret kaldırıldığında pasif kalır.
    musteri.aktif = aktif == "true"
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

    siparisler = (
        db.query(Siparis)
        .filter(Siparis.musteri_id == musteri.id)
        .all()
    )

    data = template_data(request)
    data.update({
        "musteri": musteri,
        "bekleyen_siparis": sum(s.durum == "Beklemede" for s in siparisler),
        "uretimdeki_siparis": sum(s.durum == "Üretimde" for s in siparisler),
        "tamamlanan_siparis": sum(s.durum == "Tamamlandı" for s in siparisler),
        "toplam_siparis": len(siparisler),
    })

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

    musteri = (
        db.query(Musteri)
        .filter(Musteri.id == id)
        .first()
    )

    if musteri:
        try:
            db.delete(musteri)
            db.commit()
        except IntegrityError:
            db.rollback()
            return RedirectResponse("/musteriler?error=silinemedi", status_code=303)

    return RedirectResponse(
        "/musteriler",
        status_code=303
    )
