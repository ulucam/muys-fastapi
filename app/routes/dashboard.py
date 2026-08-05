from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.context import template_data
from app.database import get_db
from app.services.dashboard_service import (
    dashboard_verisi,
    puantaj_kaydet as puantaj_kaydet_service,
)
from app.services.islem_log_service import islem_logla

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def tarihi_oku(deger: str | None) -> date:
    try:
        return datetime.strptime(deger or "", "%Y-%m-%d").date()
    except ValueError:
        return date.today()


@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    secili_tarih = date.today()
    servis_verisi = dashboard_verisi(db, secili_tarih, request.session.get("rol"), request.session.get("user_id"))
    data = template_data(request)
    data.update({
        "secili_tarih": secili_tarih,
        "bugun": date.today(),
        **servis_verisi,
    })
    return templates.TemplateResponse("dashboard/index.html", data)


@router.post("/puantaj/kaydet")
async def puantaj_kaydet(request: Request, db: Session = Depends(get_db)):
    if request.session.get("rol") == "Operatör":
        raise HTTPException(status_code=403, detail="Operatör puantaj kayıtlarını yalnızca görüntüleyebilir.")
    form = await request.form()
    secili_tarih = tarihi_oku(form.get("tarih"))
    personel_sayisi = puantaj_kaydet_service(db, secili_tarih, form, request.session.get("rol"), request.session.get("user_id"))
    islem_logla(db, request, "Puantaj", "Günlük puantaj kaydedildi", f"Tarih: {secili_tarih.isoformat()}, personel: {personel_sayisi}", commit=True)
    return RedirectResponse(f"/?tarih={secili_tarih.isoformat()}&puantaj=1#puantaj", status_code=303)
