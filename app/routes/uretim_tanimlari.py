from datetime import date, datetime

from fastapi import APIRouter, Depends, File, Request, UploadFile
from fastapi.responses import HTMLResponse, Response, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.context import template_data
from app.utils.uretim_excel import excel_dosyasini_oku, excel_sablonu_olustur as uretim_excel_sablonu_olustur
from app.database import get_db
from app.roles import PERSONEL_GORUNTULE, YONETIM
from app.security import yetki_kontrol
from app.services.uretim_tanimlari_service import (
    ana_kayit_getir,
    ekran_verisi as servis_ekran_verisi,
    excel_islemini_logla,
    excel_sablon_verisi,
    excel_verilerini_aktar,
    iliskili_kayit_getir,
    iliskili_kayit_guncelle as iliskili_kayit_guncelle_service,
    iliskili_kayit_sil as iliskili_kayit_sil_service,
    manuel_tanim_kaydet,
    personel_listesi_verisi,
    personel_puantaji,
    puantaj_listesi_verisi,
    tanim_listesi,
    tanim_sil as tanim_sil_service,
)

router = APIRouter(tags=["Üretim Tanımları"])
templates = Jinja2Templates(directory="app/templates")


def ekran_verisi(request: Request, db: Session, **ek):
    """Ortak template verisini üretim tanımları servis verisiyle birleştirir."""
    data = template_data(request)
    data.update(servis_ekran_verisi(db, **ek))
    return data


@router.get("/personeller", response_class=HTMLResponse)
def personel_listesi(
    request: Request,
    sekme: str = "personel",
    tarih: str | None = None,
    devamsiz: bool = False,
    q: str = "",
    departman: str = "",
    gorev: str = "",
    istasyon_id: int | None = None,
    db: Session = Depends(get_db),
    yetki=Depends(yetki_kontrol(PERSONEL_GORUNTULE)),
):
    try:
        secili_tarih = datetime.strptime(tarih or "", "%Y-%m-%d").date()
    except ValueError:
        secili_tarih = date.today()
    data = template_data(request)
    data.update(personel_listesi_verisi(db, q, departman, gorev, istasyon_id))
    data.update(puantaj_listesi_verisi(db, secili_tarih, devamsiz))
    data["aktif_sekme"] = "puantaj" if sekme == "puantaj" else "personel"
    return templates.TemplateResponse("uretim/personeller.html", data)


@router.get("/uretim-tanimlari", response_class=HTMLResponse)
def uretim_tanimlari(request: Request, error: str | None = None, goster: str = "", db: Session = Depends(get_db), yetki=Depends(yetki_kontrol(YONETIM))):
    hata = request.session.pop("uretim_tanim_hatasi", None)
    if error and not hata:
        hata = "Kayıt kaydedilemedi. Zorunlu alanları ve seçilen ilişkileri kontrol edin."
    baslik, kayitlar = tanim_listesi(db, goster)
    return templates.TemplateResponse("uretim/tanimlar.html", ekran_verisi(request, db, hata=hata, goster=goster, liste_basligi=baslik, secili_kayitlar=kayitlar))


@router.get("/uretim-tanimlari/personel/{personel_id}/puantaj", response_class=HTMLResponse)
def personel_puantaj_gecmisi(personel_id: int, request: Request, db: Session = Depends(get_db), yetki=Depends(yetki_kontrol(YONETIM))):
    personel, puantajlar = personel_puantaji(db, personel_id)
    if not personel:
        return RedirectResponse("/uretim-tanimlari?goster=personeller", status_code=303)
    data = template_data(request)
    data.update({"personel": personel, "puantajlar": puantajlar})
    return templates.TemplateResponse("uretim/personel_puantaj.html", data)


@router.get("/uretim-tanimlari/duzenle/{tip}/{kod}", response_class=HTMLResponse)
def duzenle_form(tip: str, kod: str, request: Request, db: Session = Depends(get_db), yetki=Depends(yetki_kontrol(YONETIM))):
    kayit = ana_kayit_getir(db, tip, kod)
    if not kayit:
        return RedirectResponse("/uretim-tanimlari", status_code=303)
    data = ekran_verisi(request, db)
    data.update({"duzenle_tipi": tip, "kayit": kayit})
    return templates.TemplateResponse("uretim/duzenle.html", data)


@router.post("/uretim-tanimlari/sil/{tip}/{kod}")
def tanim_sil(tip: str, kod: str, db: Session = Depends(get_db), yetki=Depends(yetki_kontrol(YONETIM))):
    if not tanim_sil_service(db, tip, kod):
        return RedirectResponse("/uretim-tanimlari", status_code=303)
    return RedirectResponse(f"/uretim-tanimlari?goster={'istasyonlar' if tip == 'istasyon' else 'makineler'}", status_code=303)


@router.get("/uretim-tanimlari/kayit-duzenle/{tip}/{kayit_id}", response_class=HTMLResponse)
def iliskili_kayit_duzenle(tip: str, kayit_id: int, request: Request, db: Session = Depends(get_db), yetki=Depends(yetki_kontrol(YONETIM))):
    kayit, secili_makine_idleri = iliskili_kayit_getir(db, tip, kayit_id)
    if not kayit:
        return RedirectResponse("/uretim-tanimlari", status_code=303)
    data = ekran_verisi(request, db, kayit=kayit, kayit_tipi=tip)
    data["secili_makine_idleri"] = secili_makine_idleri
    return templates.TemplateResponse("uretim/iliskili_duzenle.html", data)


@router.post("/uretim-tanimlari/kayit-duzenle/{tip}/{kayit_id}")
async def iliskili_kayit_guncelle_route(tip: str, kayit_id: int, request: Request, db: Session = Depends(get_db), yetki=Depends(yetki_kontrol(YONETIM))):
    form = await request.form()
    donus = iliskili_kayit_guncelle_service(db, tip, kayit_id, form)
    if donus:
        return RedirectResponse(f"/uretim-tanimlari?goster={donus}", status_code=303)
    return RedirectResponse(f"/uretim-tanimlari/kayit-duzenle/{tip}/{kayit_id}?error=1", status_code=303)


@router.post("/uretim-tanimlari/kayit-sil/{tip}/{kayit_id}")
def iliskili_kayit_sil_route(tip: str, kayit_id: int, db: Session = Depends(get_db), yetki=Depends(yetki_kontrol(YONETIM))):
    donus = iliskili_kayit_sil_service(db, tip, kayit_id)
    return RedirectResponse(f"/uretim-tanimlari?goster={donus}", status_code=303)


@router.post("/uretim-tanimlari/kaydet/{tip}")
async def manuel_kaydet(tip: str, request: Request, db: Session = Depends(get_db), yetki=Depends(yetki_kontrol(YONETIM))):
    form = await request.form()
    donus, hata = manuel_tanim_kaydet(
        db, tip, form, request.session.get("rol"),
        request.session.get("kullanici_adi", "Sistem"),
        request.client.host if request.client else "",
    )
    if hata:
        request.session["uretim_tanim_hatasi"] = hata
        ayirici = "&" if "?" in donus else "?"
        return RedirectResponse(f"{donus}{ayirici}error=kayit", status_code=303)
    return RedirectResponse(donus, status_code=303)


@router.get("/uretim-tanimlari/excel-sablon")
def excel_sablon(request: Request, db: Session = Depends(get_db), yetki=Depends(yetki_kontrol(YONETIM))):
    dosya = uretim_excel_sablonu_olustur(excel_sablon_verisi(db))
    excel_islemini_logla(
        db, request.session.get("kullanici_adi", "Sistem"),
        request.client.host if request.client else "", "Üretim Excel şablonu indirildi",
        "Personel, istasyon, makine, ürün sınıfı ve reçete şablonu",
    )
    return Response(dosya, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": "attachment; filename=muys-uretim-ana-veri.xlsx"})


@router.post("/uretim-tanimlari/excel-aktar", response_class=HTMLResponse)
async def excel_aktar(request: Request, file: UploadFile = File(...), db: Session = Depends(get_db), yetki=Depends(yetki_kontrol(YONETIM))):
    dosya_adi = file.filename or "adsız dosya"
    try:
        if not dosya_adi.lower().endswith(".xlsx"):
            raise ValueError("Yalnızca .xlsx dosyası yüklenebilir")
        veriler = excel_dosyasini_oku(await file.read())
        toplam, hata = excel_verilerini_aktar(
            db, veriler, dosya_adi, request.session.get("kullanici_adi", "Sistem"),
            request.client.host if request.client else "",
        )
    except Exception as hata_nesnesi:
        toplam, hata = 0, str(hata_nesnesi)
        excel_islemini_logla(
            db, request.session.get("kullanici_adi", "Sistem"),
            request.client.host if request.client else "", "Üretim Excel aktarımı başarısız",
            f"Dosya: {dosya_adi}. {type(hata_nesnesi).__name__}: {hata_nesnesi}",
        )
    if hata:
        return templates.TemplateResponse("uretim/tanimlar.html", ekran_verisi(request, db, hata=hata))
    return templates.TemplateResponse("uretim/tanimlar.html", ekran_verisi(request, db, basari=f"{toplam} satır başarıyla işlendi."))
