from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.context import template_data
from app.database import get_db
from app.roles import SIPARIS, SIPARIS_YONET
from app.security import yetki_kontrol
from app.services.siparis_service import SIPARIS_DURUMLARI, siparis_form_verisi, siparis_formunu_kaydet, siparis_liste_ekrani_verisi


router = APIRouter(tags=["Siparişler"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/siparisler", response_class=HTMLResponse)
def siparisler(
    request: Request,
    durum: str | None = None,
    giris: bool = False,
    db: Session = Depends(get_db),
    yetki=Depends(yetki_kontrol(SIPARIS)),
):
    data = template_data(request)
    data.update({
        "siparis_duzenleyebilir": request.session.get("rol") in SIPARIS_YONET,
        "siparis_giris_acik": giris and request.session.get("rol") in SIPARIS_YONET,
        **siparis_liste_ekrani_verisi(db, durum),
    })
    if data["siparis_giris_acik"]:
        data.update(siparis_form_verisi(db))
    return templates.TemplateResponse("siparisler/index.html", data)


@router.post("/siparisler/kaydet")
async def siparis_kaydet(request: Request, db: Session = Depends(get_db), yetki=Depends(yetki_kontrol(SIPARIS_YONET))):
    try:
        siparis_formunu_kaydet(db, None, await request.form())
    except (TypeError, ValueError):
        return RedirectResponse("/siparisler?error=1#module-siparis-giris", status_code=303)
    return RedirectResponse("/siparisler?kaydedildi=1#module-siparis-giris", status_code=303)


@router.get("/siparisler/{siparis_id}/duzenle", response_class=HTMLResponse)
def siparis_duzenle(siparis_id: int, request: Request, db: Session = Depends(get_db), yetki=Depends(yetki_kontrol(SIPARIS_YONET))):
    data = siparis_form_verisi(db, siparis_id)
    if not data["siparis"]:
        return RedirectResponse("/siparisler", status_code=303)
    data.update(template_data(request))
    data["durumlar"] = SIPARIS_DURUMLARI
    return templates.TemplateResponse("siparisler/duzenle.html", data)


@router.post("/siparisler/{siparis_id}/guncelle")
async def siparis_guncelle(siparis_id: int, request: Request, db: Session = Depends(get_db), yetki=Depends(yetki_kontrol(SIPARIS_YONET))):
    try:
        siparis_formunu_kaydet(db, siparis_id, await request.form())
    except (TypeError, ValueError):
        return RedirectResponse(f"/siparisler/{siparis_id}/duzenle?error=1", status_code=303)
    return RedirectResponse("/siparisler?kaydedildi=1#module-siparis-giris", status_code=303)
