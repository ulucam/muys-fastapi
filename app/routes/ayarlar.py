import io
import json
from pathlib import Path

import openpyxl
from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, Response, RedirectResponse
from fastapi.templating import Jinja2Templates
from openpyxl.worksheet.datavalidation import DataValidation
from sqlalchemy.orm import Session

from app.context import template_data
from app.database import get_db
from app.models.musteri import Musteri
from app.models.firma_ayarlari import FirmaAyarlari

router = APIRouter()

templates = Jinja2Templates(
    directory="app/templates"
)

ILLER_DOSYASI = Path(__file__).resolve().parent.parent / "data" / "iller.js"
MUSTERI_SUTUNLARI = ["Firma Adı", "Yetkili", "Telefon", "E-Posta", "Vergi Dairesi", "Vergi No", "İl", "İlçe", "Müşteri Türü", "Adres", "Açıklama"]
TURLER = ["Alıcı", "Tedarikçi", "Satıcı"]


def il_ilce_verisi():
    with ILLER_DOSYASI.open(encoding="utf-8") as dosya:
        return json.load(dosya)


def metin(deger):
    return str(deger or "").strip()


def excel_satirlarini_oku(dosya_icerigi):
    kitap = openpyxl.load_workbook(io.BytesIO(dosya_icerigi), data_only=True)
    if "Müşteriler" not in kitap.sheetnames:
        return [], ["'Müşteriler' sayfası bulunamadı."]
    sayfa = kitap["Müşteriler"]
    basliklar = [metin(hucre.value) for hucre in sayfa[1]]
    if basliklar[:len(MUSTERI_SUTUNLARI)] != MUSTERI_SUTUNLARI:
        return [], ["Müşteriler sayfasındaki sütun başlıkları taslakla uyuşmuyor."]

    iller = il_ilce_verisi()
    satirlar, hatalar = [], []
    for sira, satir in enumerate(sayfa.iter_rows(min_row=2, values_only=True), start=2):
        if not any(satir):
            continue
        veri = dict(zip(MUSTERI_SUTUNLARI, map(metin, satir)))
        satir_hatalari = []
        if not veri["Firma Adı"]:
            satir_hatalari.append("Firma adı zorunlu")
        if veri["Müşteri Türü"] not in TURLER:
            satir_hatalari.append("Müşteri türü Alıcı, Tedarikçi veya Satıcı olmalı")
        if veri["İl"] and veri["İl"] not in iller:
            satir_hatalari.append("Geçersiz il")
        if veri["İlçe"] and (not veri["İl"] or veri["İlçe"] not in iller.get(veri["İl"], [])):
            satir_hatalari.append("İlçenin seçilen ille eşleşmesi gerekiyor")
        if satir_hatalari:
            hatalar.append(f"Satır {sira}: {', '.join(satir_hatalari)}")
        else:
            satirlar.append(veri)
    return satirlar, hatalar


@router.get("/ayarlar", response_class=HTMLResponse)
async def ayarlar(request: Request):

    return templates.TemplateResponse(
        "ayarlar/index.html",
        template_data(request)
    )


@router.get("/ayarlar/excel", response_class=HTMLResponse)
async def excel(request: Request):

    return templates.TemplateResponse(
        "ayarlar/excel.html",
        template_data(request)
    )


@router.get("/ayarlar/excel/sablon")
def excel_sablon(db: Session = Depends(get_db)):
    iller = il_ilce_verisi()
    firma = db.query(FirmaAyarlari).first()
    mevcut_musteriler = db.query(Musteri).order_by(Musteri.id).all()
    kitap = openpyxl.Workbook()
    sistem = kitap.active
    sistem.title = "Sistem Bilgileri"
    sistem.append(["MÜYS Müşteri Aktarım ve Dışa Aktarma"])
    sistem.append(["Açıklama", "Firma bilgileri ve mevcut müşteri kayıtları dışa aktarıldı; müşteri kayıtları ikinci sayfada yer alır."])
    sistem.append(["Kurallar", "Firma adı zorunludur. İl, ilçe ve müşteri türü açılır listelerden seçilmelidir."])
    sistem.append([])
    sistem.append(["Firma Bilgileri"])
    for etiket, alan in [("Firma Adı", "firma_adi"), ("Vergi No", "vergi_no"), ("Vergi Dairesi", "vergi_dairesi"), ("Telefon", "telefon"), ("E-Posta", "email"), ("Web Sitesi", "web_sitesi"), ("Adres", "adres")]:
        sistem.append([etiket, getattr(firma, alan, "") if firma else ""])
    sistem.column_dimensions["A"].width = 28
    sistem.column_dimensions["B"].width = 100
    for hucre in sistem[1]:
        hucre.font = openpyxl.styles.Font(bold=True, size=14, color="FFFFFF")
        hucre.fill = openpyxl.styles.PatternFill("solid", fgColor="1F4E78")

    musteriler = kitap.create_sheet("Müşteriler")
    musteriler.append(MUSTERI_SUTUNLARI)
    for musteri in mevcut_musteriler:
        musteriler.append([
            musteri.firma_adi, musteri.yetkili, musteri.telefon, musteri.email,
            musteri.vergi_dairesi, musteri.vergi_no, musteri.il, musteri.ilce,
            musteri.musteri_turu or "Alıcı", musteri.adres, musteri.aciklama,
        ])
    musteriler.freeze_panes = "A2"
    son_satir = max(501, len(mevcut_musteriler) + 1)
    musteriler.auto_filter.ref = f"A1:K{son_satir}"
    for hucre in musteriler[1]:
        hucre.font = openpyxl.styles.Font(bold=True, color="FFFFFF")
        hucre.fill = openpyxl.styles.PatternFill("solid", fgColor="1F4E78")
    for sutun, genislik in zip("ABCDEFGHIJK", [28, 22, 18, 28, 20, 16, 18, 20, 18, 45, 35]):
        musteriler.column_dimensions[sutun].width = genislik

    listeler = kitap.create_sheet("Listeler")
    listeler.append(["İller", "İlçeler", "Müşteri Türleri"])
    tum_ilceler = sorted({ilce for ilceler in iller.values() for ilce in ilceler})
    for sira in range(max(len(iller), len(tum_ilceler), len(TURLER))):
        listeler.append([
            sorted(iller)[sira] if sira < len(iller) else None,
            tum_ilceler[sira] if sira < len(tum_ilceler) else None,
            TURLER[sira] if sira < len(TURLER) else None,
        ])
    listeler.sheet_state = "hidden"
    for formül, alan in [("'Listeler'!$A$2:$A$82", f"G2:G{son_satir}"), (f"'Listeler'!$B$2:$B${len(tum_ilceler) + 1}", f"H2:H{son_satir}"), ("'Listeler'!$C$2:$C$4", f"I2:I{son_satir}")]:
        dogrulama = DataValidation(type="list", formula1=formül, allow_blank=True)
        musteriler.add_data_validation(dogrulama)
        dogrulama.add(alan)

    akis = io.BytesIO()
    kitap.save(akis)
    return Response(
        akis.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=muys-musteri-aktarim-taslagi.xlsx"},
    )


@router.post("/ayarlar/excel/onizleme", response_class=HTMLResponse)
async def excel_onizleme(request: Request, file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        satirlar, hatalar = excel_satirlarini_oku(await file.read())
    except Exception:
        satirlar, hatalar = [], ["Excel dosyası okunamadı. Lütfen taslağı kullanın."]

    mevcutlar = {m.firma_adi.casefold(): m for m in db.query(Musteri).all()}
    eklenecek, guncellenecek = [], []
    for satir in satirlar:
        (guncellenecek if satir["Firma Adı"].casefold() in mevcutlar else eklenecek).append(satir["Firma Adı"])
    request.session["excel_onay"] = satirlar if not hatalar else []

    data = template_data(request)
    data.update({"hatalar": hatalar, "eklenecek": eklenecek, "guncellenecek": guncellenecek, "gecerli_satir": len(satirlar)})
    return templates.TemplateResponse("ayarlar/excel.html", data)


@router.post("/ayarlar/excel/onayla")
def excel_onayla(request: Request, db: Session = Depends(get_db)):
    satirlar = request.session.pop("excel_onay", [])
    if not satirlar:
        return RedirectResponse("/ayarlar/excel", status_code=303)
    for satir in satirlar:
        musteri = db.query(Musteri).filter(Musteri.firma_adi.ilike(satir["Firma Adı"])).first()
        if not musteri:
            son = db.query(Musteri).order_by(Musteri.id.desc()).first()
            musteri = Musteri(musteri_kodu=f"M{(son.id + 1) if son else 1:06}")
            db.add(musteri)
        musteri.firma_adi = satir["Firma Adı"]
        musteri.yetkili = satir["Yetkili"]
        musteri.telefon = satir["Telefon"]
        musteri.email = satir["E-Posta"]
        musteri.vergi_dairesi = satir["Vergi Dairesi"]
        musteri.vergi_no = satir["Vergi No"]
        musteri.il, musteri.ilce = satir["İl"], satir["İlçe"]
        musteri.musteri_turu = satir["Müşteri Türü"]
        musteri.adres, musteri.aciklama = satir["Adres"], satir["Açıklama"]
    db.commit()
    return RedirectResponse("/ayarlar/excel", status_code=303)


@router.get("/ayarlar/yedek", response_class=HTMLResponse)
async def yedek(request: Request):

    return templates.TemplateResponse(
        "ayarlar/yedek.html",
        template_data(request)
    )


@router.get("/ayarlar/loglar", response_class=HTMLResponse)
async def loglar(request: Request):

    return templates.TemplateResponse(
        "ayarlar/loglar.html",
        template_data(request)
    )


@router.get("/ayarlar/firma", response_class=HTMLResponse)
async def firma(request: Request, db: Session = Depends(get_db)):
    data = template_data(request)
    data["firma"] = db.query(FirmaAyarlari).first()

    return templates.TemplateResponse("ayarlar/firma.html", data)


@router.post("/ayarlar/firma")
async def firma_kaydet(
    firma_adi: str = Form(""), vergi_no: str = Form(""),
    vergi_dairesi: str = Form(""), telefon: str = Form(""),
    email: str = Form(""), web_sitesi: str = Form(""), adres: str = Form(""),
    db: Session = Depends(get_db),
):
    firma = db.query(FirmaAyarlari).first()
    if not firma:
        firma = FirmaAyarlari()
        db.add(firma)
    firma.firma_adi, firma.vergi_no = firma_adi, vergi_no
    firma.vergi_dairesi, firma.telefon = vergi_dairesi, telefon
    firma.email, firma.web_sitesi, firma.adres = email, web_sitesi, adres
    db.commit()

    return RedirectResponse("/ayarlar/firma", status_code=303)


@router.get("/ayarlar/sistem", response_class=HTMLResponse)
async def sistem(request: Request):

    return templates.TemplateResponse(
        "ayarlar/sistem.html",
        template_data(request)
    )
