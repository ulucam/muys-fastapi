from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.context import template_data
from app.database import get_db
from app.roles import SIPARIS
from app.security import yetki_kontrol
from app.services.siparis_service import SIPARIS_DURUMLARI, siparis_form_verisi, siparis_formunu_kaydet, siparis_sayfasi_verisi


router = APIRouter(tags=["Siparişler"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/siparisler", response_class=HTMLResponse)
def siparisler(
    request: Request,
    musteri_id: int | None = None,
    durum: str | None = None,
    db: Session = Depends(get_db),
    yetki=Depends(yetki_kontrol(SIPARIS)),
):
    musteri, siparisler_duruma_gore = siparis_sayfasi_verisi(db, musteri_id, durum)
    durumlar = list(SIPARIS_DURUMLARI)
    data = template_data(request)
    data.update({
        "musteri_id": musteri_id,
        "musteri": musteri,
        "durum": durum,
        "durumlar": durumlar,
        "siparisler_duruma_gore": siparisler_duruma_gore,
        **siparis_form_verisi(db),
    })
    return templates.TemplateResponse("siparisler/index.html", data)


@router.post("/siparisler/kaydet")
async def siparis_kaydet(request: Request, db: Session = Depends(get_db), yetki=Depends(yetki_kontrol(SIPARIS))):
    try:
        siparis_formunu_kaydet(db, None, await request.form())
    except (TypeError, ValueError):
        return RedirectResponse("/siparisler?error=1#module-siparis-giris", status_code=303)
    return RedirectResponse("/siparisler?kaydedildi=1#module-siparis-giris", status_code=303)


@router.get("/siparisler/{siparis_id}/duzenle", response_class=HTMLResponse)
def siparis_duzenle(siparis_id: int, request: Request, db: Session = Depends(get_db), yetki=Depends(yetki_kontrol(SIPARIS))):
    data = siparis_form_verisi(db, siparis_id)
    if not data["siparis"]:
        return RedirectResponse("/siparisler", status_code=303)
    data.update(template_data(request))
    data["durumlar"] = SIPARIS_DURUMLARI
    return templates.TemplateResponse("siparisler/duzenle.html", data)


@router.post("/siparisler/{siparis_id}/guncelle")
async def siparis_guncelle(siparis_id: int, request: Request, db: Session = Depends(get_db), yetki=Depends(yetki_kontrol(SIPARIS))):
    try:
        siparis_formunu_kaydet(db, siparis_id, await request.form())
    except (TypeError, ValueError):
        return RedirectResponse(f"/siparisler/{siparis_id}/duzenle?error=1", status_code=303)
    return RedirectResponse("/siparisler?kaydedildi=1#module-siparis-giris", status_code=303)
