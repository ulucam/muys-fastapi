from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, Response, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.utils.excel import (
    excel_satirlarini_oku,
    excel_sablonu_olustur,
)

from app.context import template_data
from app.database import get_db
from app.roles import ADMIN
from app.security import yetki_kontrol
from app.services.ayarlar_service import (
    excel_indirme_logu,
    excel_sablon_verileri,
    firma_bilgilerini_kaydet,
    firma_getir,
    loglari_listele,
    son_excel_aktarimi,
)
from app.services.excel_aktarim_service import (
    aktarimi_onayla,
    onizleme_hatasini_logla,
    onizleme_hazirla,
)
from app.services.islem_log_service import son_kullanici_hareketleri
from app.services.sistem_service import sistem_bilgileri

router = APIRouter()

templates = Jinja2Templates(
    directory="app/templates"
)


@router.get("/api/islem-loglari/son")
def son_islem_hareketleri(
    db: Session = Depends(get_db),
    yetki=Depends(yetki_kontrol(ADMIN)),
):
    return JSONResponse({"hareketler": son_kullanici_hareketleri(db)})

@router.get("/ayarlar", response_class=HTMLResponse)
async def ayarlar(request: Request):

    return templates.TemplateResponse(
        "ayarlar/index.html",
        template_data(request)
    )


@router.get("/ayarlar/excel", response_class=HTMLResponse)
async def excel(request: Request, db: Session = Depends(get_db)):
    data = template_data(request)
    data["son_aktarim"] = son_excel_aktarimi(db)
    return templates.TemplateResponse(
        "ayarlar/excel.html",
        data
    )


@router.get("/ayarlar/excel/sablon")
def excel_sablon(request: Request, db: Session = Depends(get_db)):
    sablon_verisi = excel_sablon_verileri(db)
    mevcut_musteriler = sablon_verisi["musteriler"]
    mevcut_urunler = sablon_verisi["urunler"]
    mevcut_personeller = sablon_verisi["personeller"]
    mevcut_istasyonlar = sablon_verisi["istasyonlar"]
    mevcut_makineler = sablon_verisi["makineler"]
    dosya_icerigi = excel_sablonu_olustur(sablon_verisi)
    excel_indirme_logu(
        db,
        request.session.get("kullanici_adi", "Sistem"),
        request.client.host if request.client else "",
        f"{len(mevcut_musteriler)} müşteri, {len(mevcut_urunler)} stok ürünü, {len(mevcut_personeller)} personel, {len(mevcut_istasyonlar)} istasyon ve {len(mevcut_makineler)} makine dışa aktarıldı",
    )
    return Response(
        dosya_icerigi,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": "attachment; filename=muys-aktarim-ve-listeler.xlsx",
            "Cache-Control": "no-store, no-cache, max-age=0",
        },
    )


@router.post("/ayarlar/excel/onizleme", response_class=HTMLResponse)
async def excel_onizleme(request: Request, file: UploadFile = File(...), db: Session = Depends(get_db)):
    dosya_adi = file.filename or "adsız dosya"
    kullanici_adi = request.session.get("kullanici_adi", "Sistem")
    ip_adresi = request.client.host if request.client else ""
    if not dosya_adi.lower().endswith(".xlsx"):
        hatalar = ["Yalnızca .xlsx uzantılı Excel dosyaları yüklenebilir."]
        satirlar, urunler, personeller, istasyonlar, makineler = [], [], [], [], []
    else:
        try:
            dosya_icerigi = await file.read()
            if not dosya_icerigi:
                raise ValueError("Dosya boş")
            satirlar, urunler, personeller, istasyonlar, makineler, hatalar = excel_satirlarini_oku(dosya_icerigi)
        except Exception as hata:
            satirlar, urunler, personeller, istasyonlar, makineler = [], [], [], [], []
            hatalar = [f"Excel dosyası okunamadı: {type(hata).__name__}. Ayrıntı işlem geçmişine kaydedildi."]
            onizleme_hatasini_logla(db, dosya_adi, hata, kullanici_adi, ip_adresi)

    sonuc = onizleme_hazirla(
        db, dosya_adi, satirlar, urunler, personeller, istasyonlar, makineler, hatalar,
        request.session.get("excel_onay_token"), kullanici_adi, ip_adresi,
    )
    if sonuc["token"]:
        request.session["excel_onay_token"] = sonuc["token"]

    data = template_data(request)
    data["son_aktarim"] = son_excel_aktarimi(db)
    data.update({alan: deger for alan, deger in sonuc.items() if alan != "token"})
    return templates.TemplateResponse("ayarlar/excel.html", data)


@router.post("/ayarlar/excel/onayla")
def excel_onayla(request: Request, db: Session = Depends(get_db)):
    token = request.session.get("excel_onay_token")
    if aktarimi_onayla(
        db, token, request.session.get("kullanici_adi", "Sistem"),
        request.client.host if request.client else "",
    ):
        request.session.pop("excel_onay_token", None)
    return RedirectResponse("/ayarlar/excel", status_code=303)


@router.get("/ayarlar/yedek", response_class=HTMLResponse)
async def yedek(request: Request):

    return templates.TemplateResponse(
        "ayarlar/yedek.html",
        template_data(request)
    )


@router.get("/ayarlar/loglar", response_class=HTMLResponse)
async def loglar(
    request: Request,
    db: Session = Depends(get_db),
    yetki=Depends(yetki_kontrol(ADMIN)),
):
    data = template_data(request)
    data["loglar"] = loglari_listele(db)

    return templates.TemplateResponse("ayarlar/loglar.html", data)


@router.get("/ayarlar/firma", response_class=HTMLResponse)
async def firma(request: Request, db: Session = Depends(get_db)):
    data = template_data(request)
    data["firma"] = firma_getir(db)

    return templates.TemplateResponse("ayarlar/firma.html", data)


@router.post("/ayarlar/firma")
async def firma_kaydet(
    request: Request,
    firma_adi: str = Form(""), vergi_no: str = Form(""),
    vergi_dairesi: str = Form(""), telefon: str = Form(""),
    email: str = Form(""), web_sitesi: str = Form(""), adres: str = Form(""), logo: UploadFile | None = File(None),
    db: Session = Depends(get_db),
):
    try:
        logo_dosyasi = ((logo.filename or "logo"), await logo.read()) if logo and logo.filename else None
        firma_bilgilerini_kaydet(
            db,
            request.session.get("kullanici_adi", "Sistem"),
            request.client.host if request.client else "",
            logo_dosyasi=logo_dosyasi,
            firma_adi=firma_adi,
            vergi_no=vergi_no,
            vergi_dairesi=vergi_dairesi,
            telefon=telefon,
            email=email,
            web_sitesi=web_sitesi,
            adres=adres,
        )
    except ValueError as hata:
        data = template_data(request)
        data.update({"firma": firma_getir(db), "hata": str(hata)})
        return templates.TemplateResponse("ayarlar/firma.html", data, status_code=400)

    return RedirectResponse("/ayarlar/firma", status_code=303)


@router.get("/ayarlar/sistem", response_class=HTMLResponse)
async def sistem(request: Request):
    data = template_data(request)
    data["sistem_bilgileri"] = sistem_bilgileri()
    return templates.TemplateResponse("ayarlar/sistem.html", data)
