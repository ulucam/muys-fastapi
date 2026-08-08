from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.context import template_data
from app.database import get_db
from app.roles import STOK
from app.security import yetki_kontrol
from app.services.stok_service import (
    hammaddeleri_listele,
    hammaddeleri_filtrele,
    receteleri_listele,
    stok_sinifi_kaydet,
    stok_sinifi_sil,
    stok_tanim_kullanimlari,
    stok_kurulum_durumu,
    stok_tanimlari,
    stok_tum_tanimlari,
    stok_turu_kaydet,
    stok_turu_sil,
    stok_urunu_kaydet,
    stok_urunlerini_toplu_guncelle,
    stok_urunlerini_listele,
)
from app.services.uretim_plan_service import (
    asama_malzemesi_sil,
    asama_malzemesi_kaydet,
    recete_asamasi_guncelle,
    recete_asamasi_sil,
    recete_asamasi_kaydet,
    recete_duzenleme_verisi,
    recete_guncelle,
    recete_kaydet,
    uretim_tanim_verisi,
)

router = APIRouter(tags=["Stok"])
templates = Jinja2Templates(directory="app/templates")


def _opsiyonel_id(deger: str) -> int | None:
    """Boş seçmeli filtre alanlarını sayı doğrulamasına takılmadan işler."""
    try:
        return int(deger) if str(deger or "").strip() else None
    except (TypeError, ValueError):
        return None


@router.get("/stok", response_class=HTMLResponse)
def stok_listesi(request: Request, db: Session = Depends(get_db), yetki=Depends(yetki_kontrol(STOK))):
    data = template_data(request)
    data["urunler"] = stok_urunlerini_listele(db)
    data["turler"], data["siniflar"] = stok_tum_tanimlari(db)
    return templates.TemplateResponse("stok/urun_listesi.html", data)


@router.get("/urunler")
def urunler_eski_adres(yetki=Depends(yetki_kontrol(STOK))):
    """Önceki menü bağlantıları için stok listesine güvenli yönlendirme."""
    return RedirectResponse("/stok", status_code=303)


@router.post("/urunler")
def urun_kaydet(
    kodu: str = Form(""), adi: str = Form(""), stok_urun_turu_id: int = Form(...),
    stok_urun_sinifi_id: int | None = Form(None), birim: str = Form("Adet"),
    marka: str = Form(""), model: str = Form(""), mevcut_stok: int = Form(0),
    min_stok: int = Form(0), urun_id: int | None = Form(None),
    db: Session = Depends(get_db), yetki=Depends(yetki_kontrol(STOK)),
):
    try:
        stok_urunu_kaydet(db, kodu, adi, stok_urun_turu_id, stok_urun_sinifi_id, birim, marka, model, mevcut_stok, min_stok, urun_id)
    except ValueError:
        return RedirectResponse("/receteler?error=urun#module-yeni-kart", status_code=303)
    return RedirectResponse("/receteler#module-stoklar", status_code=303)


@router.post("/urunler/tur/kaydet")
def tur_kaydet(adi: str = Form(""), db: Session = Depends(get_db), yetki=Depends(yetki_kontrol(STOK))):
    try:
        stok_turu_kaydet(db, adi)
    except ValueError:
        return RedirectResponse("/receteler?error=tur#module-tanimlar", status_code=303)
    return RedirectResponse("/receteler#module-tanimlar", status_code=303)


@router.post("/urunler/tur/{tur_id}/guncelle")
def tur_guncelle(tur_id: int, adi: str = Form(""), db: Session = Depends(get_db), yetki=Depends(yetki_kontrol(STOK))):
    try:
        stok_turu_kaydet(db, adi, tur_id)
    except ValueError:
        return RedirectResponse("/receteler?error=tur#module-tanimlar", status_code=303)
    return RedirectResponse("/receteler#module-tanimlar", status_code=303)


@router.post("/urunler/tur/{tur_id}/sil")
def tur_sil(tur_id: int, urunlerden_kaldir: bool = Form(False), db: Session = Depends(get_db), yetki=Depends(yetki_kontrol(STOK))):
    try:
        stok_turu_sil(db, tur_id, urunlerden_kaldir)
    except ValueError:
        return RedirectResponse("/receteler?error=tur_kullanim#module-tanimlar", status_code=303)
    return RedirectResponse("/receteler#module-tanimlar", status_code=303)


@router.post("/urunler/sinif/kaydet")
def sinif_kaydet(adi: str = Form(""), db: Session = Depends(get_db), yetki=Depends(yetki_kontrol(STOK))):
    try:
        stok_sinifi_kaydet(db, adi)
    except ValueError:
        return RedirectResponse("/receteler?error=sinif#module-tanimlar", status_code=303)
    return RedirectResponse("/receteler#module-tanimlar", status_code=303)


@router.post("/urunler/sinif/{sinif_id}/guncelle")
def sinif_guncelle(sinif_id: int, adi: str = Form(""), db: Session = Depends(get_db), yetki=Depends(yetki_kontrol(STOK))):
    try:
        stok_sinifi_kaydet(db, adi, sinif_id)
    except ValueError:
        return RedirectResponse("/receteler?error=sinif#module-tanimlar", status_code=303)
    return RedirectResponse("/receteler#module-tanimlar", status_code=303)


@router.post("/urunler/sinif/{sinif_id}/sil")
def sinif_sil(sinif_id: int, urunlerden_kaldir: bool = Form(False), db: Session = Depends(get_db), yetki=Depends(yetki_kontrol(STOK))):
    try:
        stok_sinifi_sil(db, sinif_id, urunlerden_kaldir)
    except ValueError:
        return RedirectResponse("/receteler?error=sinif_kullanim#module-tanimlar", status_code=303)
    return RedirectResponse("/receteler#module-tanimlar", status_code=303)


@router.get("/receteler", response_class=HTMLResponse)
def receteler(request: Request, error: str | None = None, q: str = "", urun_id: str = "", tur_id: str = "", sinif_id: str = "", db: Session = Depends(get_db), yetki=Depends(yetki_kontrol(STOK))):
    urun_id, tur_id, sinif_id = _opsiyonel_id(urun_id), _opsiyonel_id(tur_id), _opsiyonel_id(sinif_id)
    data = template_data(request)
    data["receteler"] = receteleri_listele(db)
    data["urunler"] = hammaddeleri_filtrele(db, q, urun_id, tur_id, sinif_id)
    data["turler"], data["siniflar"] = stok_tanimlari(db)
    data["kurulum"] = stok_kurulum_durumu(db)
    data["tanim_kullanimlari"] = stok_tanim_kullanimlari(db)
    data.update(uretim_tanim_verisi(db))
    kullanim_hatasi = error in ("tur_kullanim", "sinif_kullanim")
    data["hata"] = ("Tanım ürünlerde kullanılıyor. Ürünlerden kaldırıp sil seçeneğini kullanın." if kullanim_hatasi else "Kayıt yapılamadı. Zorunlu alanları ve benzersiz ad/kod bilgisini kontrol edin.") if error else None
    data.update({"stok_arama": q, "stok_filtre_urunleri": hammaddeleri_listele(db), "secili_urun_id": urun_id, "secili_tur_id": tur_id, "secili_sinif_id": sinif_id})
    return templates.TemplateResponse("stok/urunler.html", data)


@router.post("/urunler/toplu-guncelle")
async def stok_urunlerini_toplu_guncelle_route(request: Request, db: Session = Depends(get_db), yetki=Depends(yetki_kontrol(STOK))):
    form = await request.form()
    try:
        stok_urunlerini_toplu_guncelle(db, form)
    except ValueError:
        return RedirectResponse("/receteler?error=toplu#module-stoklar", status_code=303)
    return RedirectResponse("/receteler?kaydedildi=toplu#module-stoklar", status_code=303)


@router.post("/receteler/kaydet")
def uretim_recetesi_kaydet(urun_id: int = Form(...), tahmini_uretim_suresi: float = Form(0), aciklama: str = Form(""),
    db: Session = Depends(get_db), yetki=Depends(yetki_kontrol(STOK))):
    try:
        recete, mevcut_recete = recete_kaydet(db, urun_id, tahmini_uretim_suresi, aciklama)
    except ValueError:
        return RedirectResponse("/receteler?error=recete#module-uretim-receteleri", status_code=303)
    if mevcut_recete:
        return RedirectResponse(f"/receteler/{recete.id}/duzenle?mevcut=1", status_code=303)
    return RedirectResponse(f"/receteler/{recete.id}/duzenle", status_code=303)


@router.get("/receteler/{recete_id}/duzenle", response_class=HTMLResponse)
def uretim_recetesi_duzenle(recete_id: int, request: Request, db: Session = Depends(get_db), yetki=Depends(yetki_kontrol(STOK))):
    data = recete_duzenleme_verisi(db, recete_id)
    if not data:
        return RedirectResponse("/receteler#module-uretim-receteleri", status_code=303)
    data.update(template_data(request))
    return templates.TemplateResponse("stok/recete_duzenle.html", data)


@router.post("/receteler/{recete_id}/guncelle")
def uretim_recetesi_guncelle(recete_id: int, urun_id: int = Form(...), tahmini_uretim_suresi: float = Form(0), aciklama: str = Form(""),
    db: Session = Depends(get_db), yetki=Depends(yetki_kontrol(STOK))):
    try:
        recete_guncelle(db, recete_id, urun_id, tahmini_uretim_suresi, aciklama)
    except ValueError:
        return RedirectResponse(f"/receteler/{recete_id}/duzenle?error=recete", status_code=303)
    return RedirectResponse(f"/receteler/{recete_id}/duzenle?kaydedildi=1", status_code=303)


@router.post("/receteler/{recete_id}/asama")
def uretim_recetesi_asama_kaydet(recete_id: int, sira_no: int = Form(...), istasyon_id: int = Form(...),
    operasyon_adi: str = Form(""), hedef_cevrim_suresi: float = Form(0), aciklama: str = Form(""), donus_duzenle: bool = Form(False),
    db: Session = Depends(get_db), yetki=Depends(yetki_kontrol(STOK))):
    try:
        recete_asamasi_kaydet(db, recete_id, sira_no, istasyon_id, operasyon_adi, hedef_cevrim_suresi, aciklama)
    except ValueError:
        if donus_duzenle:
            return RedirectResponse(f"/receteler/{recete_id}/duzenle?error=asama", status_code=303)
        return RedirectResponse("/receteler?error=asama#module-uretim-receteleri", status_code=303)
    if donus_duzenle:
        return RedirectResponse(f"/receteler/{recete_id}/duzenle?kaydedildi=1", status_code=303)
    return RedirectResponse("/receteler#module-uretim-receteleri", status_code=303)


@router.post("/receteler/{recete_id}/asama/{asama_id}/guncelle")
def uretim_recetesi_asama_guncelle(recete_id: int, asama_id: int, sira_no: int = Form(...), istasyon_id: int = Form(...),
    operasyon_adi: str = Form(""), hedef_cevrim_suresi: float = Form(0), aciklama: str = Form(""),
    db: Session = Depends(get_db), yetki=Depends(yetki_kontrol(STOK))):
    try:
        recete_asamasi_guncelle(db, recete_id, asama_id, sira_no, istasyon_id, operasyon_adi, hedef_cevrim_suresi, aciklama)
    except ValueError:
        return RedirectResponse(f"/receteler/{recete_id}/duzenle?error=asama", status_code=303)
    return RedirectResponse(f"/receteler/{recete_id}/duzenle?kaydedildi=1", status_code=303)


@router.post("/receteler/{recete_id}/asama/{asama_id}/sil")
def uretim_recetesi_asama_sil(recete_id: int, asama_id: int, db: Session = Depends(get_db), yetki=Depends(yetki_kontrol(STOK))):
    try:
        recete_asamasi_sil(db, recete_id, asama_id)
    except ValueError:
        return RedirectResponse(f"/receteler/{recete_id}/duzenle?error=asama", status_code=303)
    return RedirectResponse(f"/receteler/{recete_id}/duzenle?kaydedildi=1", status_code=303)


@router.post("/receteler/asama/{asama_id}/malzeme")
def uretim_asama_malzeme_kaydet(asama_id: int, malzeme_id: int = Form(...), miktar: float = Form(...),
    birim: str = Form("Adet"), fire_orani: float = Form(0), donus_recete_id: int | None = Form(None), db: Session = Depends(get_db),
    yetki=Depends(yetki_kontrol(STOK))):
    try:
        asama_malzemesi_kaydet(db, asama_id, malzeme_id, miktar, birim, fire_orani)
    except ValueError:
        if donus_recete_id:
            return RedirectResponse(f"/receteler/{donus_recete_id}/duzenle?error=malzeme", status_code=303)
        return RedirectResponse("/receteler?error=malzeme#module-uretim-receteleri", status_code=303)
    if donus_recete_id:
        return RedirectResponse(f"/receteler/{donus_recete_id}/duzenle?kaydedildi=1", status_code=303)
    return RedirectResponse("/receteler#module-uretim-receteleri", status_code=303)


@router.post("/receteler/{recete_id}/asama/{asama_id}/malzeme/{malzeme_id}/sil")
def uretim_asama_malzeme_sil(recete_id: int, asama_id: int, malzeme_id: int, db: Session = Depends(get_db), yetki=Depends(yetki_kontrol(STOK))):
    try:
        asama_malzemesi_sil(db, asama_id, malzeme_id)
    except ValueError:
        return RedirectResponse(f"/receteler/{recete_id}/duzenle?error=malzeme", status_code=303)
    return RedirectResponse(f"/receteler/{recete_id}/duzenle?kaydedildi=1", status_code=303)
