from fastapi import APIRouter, BackgroundTasks, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.context import template_data
from app.database import get_db
from app.services.iletisim_service import (
    aktif_kullanicilar,
    bildirimleri_okundu_yap,
    iletisim_ozeti,
    mesaj_gonder,
    mesaj_kutulari,
    mesaji_okundu_yap,
)
from app.services.push_service import arka_planda_push_gonder

router = APIRouter(tags=["İletişim"])
templates = Jinja2Templates(directory="app/templates")


def _kullanici_id(request: Request) -> int:
    kullanici_id = request.session.get("user_id")
    if not kullanici_id:
        raise HTTPException(status_code=401, detail="Oturum gerekli")
    return int(kullanici_id)


@router.get("/mesajlar", response_class=HTMLResponse)
def mesajlar(request: Request, durum: str | None = None, db: Session = Depends(get_db)):
    kullanici_id = _kullanici_id(request)
    data = template_data(request)
    data.update(mesaj_kutulari(db, kullanici_id))
    data["alici_secenekleri"] = aktif_kullanicilar(db, kullanici_id)
    data["durum"] = durum
    return templates.TemplateResponse("iletisim/index.html", data)


@router.post("/mesajlar/gonder")
def mesaj_gonder_route(request: Request, background_tasks: BackgroundTasks, alici_id: int = Form(...), konu: str = Form(""), icerik: str = Form(""), db: Session = Depends(get_db)):
    try:
        mesaj = mesaj_gonder(db, _kullanici_id(request), alici_id, konu, icerik)
    except ValueError:
        return RedirectResponse("/mesajlar?durum=hata#module-yeni", status_code=303)
    background_tasks.add_task(arka_planda_push_gonder, alici_id, "Yeni mesaj", f"{request.session.get('kullanici_adi', 'Bir kullanıcı')} size mesaj gönderdi: {mesaj.konu}", f"/mesajlar#mesaj-{mesaj.id}")
    return RedirectResponse("/mesajlar?durum=gonderildi#module-giden", status_code=303)


@router.post("/mesajlar/{mesaj_id}/okundu")
def mesaj_okundu(mesaj_id: int, request: Request, db: Session = Depends(get_db)):
    if not mesaji_okundu_yap(db, mesaj_id, _kullanici_id(request)):
        raise HTTPException(status_code=404, detail="Mesaj bulunamadı")
    return RedirectResponse(f"/mesajlar#mesaj-{mesaj_id}", status_code=303)


@router.get("/api/iletisim/ozet", response_class=JSONResponse)
def ozet(request: Request, db: Session = Depends(get_db)):
    return iletisim_ozeti(db, _kullanici_id(request))


@router.post("/api/bildirimler/okundu", response_class=JSONResponse)
def bildirim_okundu(request: Request, db: Session = Depends(get_db)):
    return {"okunan": bildirimleri_okundu_yap(db, _kullanici_id(request))}
