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
    mesaj_konulari_verisi,
    mesaj_konusu_kaydet,
    mesaj_kutulari,
    mesaji_yanitla,
    mesaji_okundu_yap,
)
from app.services.push_service import arka_planda_push_gonder
from app.roles import ADMIN
from app.security import yetki_kontrol

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
    data.update(mesaj_konulari_verisi(db))
    data["oturum_kullanici_id"] = kullanici_id
    data["alici_secenekleri"] = aktif_kullanicilar(db, kullanici_id)
    data["tum_aktif_kullanicilar"] = aktif_kullanicilar(db, 0)
    data["durum"] = durum
    return templates.TemplateResponse("iletisim/index.html", data)


@router.post("/mesajlar/gonder")
def mesaj_gonder_route(request: Request, background_tasks: BackgroundTasks, alici_id: int = Form(...), konu_id: int = Form(...), baslik: str = Form(""), icerik: str = Form(""), db: Session = Depends(get_db)):
    try:
        mesaj, hedef_idleri, mesaj_konusu = mesaj_gonder(db, _kullanici_id(request), alici_id, konu_id, baslik, icerik)
    except ValueError:
        return RedirectResponse("/mesajlar?durum=hata#module-yeni", status_code=303)
    for hedef_id in hedef_idleri:
        background_tasks.add_task(arka_planda_push_gonder, hedef_id, f"{mesaj_konusu.adi}: Yeni mesaj", f"{request.session.get('kullanici_adi', 'Bir kullanıcı')}: {mesaj.konu}", f"/mesajlar#konusma-{mesaj.id}")
    return RedirectResponse("/mesajlar?durum=gonderildi#module-giden", status_code=303)


@router.post("/mesajlar/{mesaj_id}/yanitla")
def mesaj_yanitla_route(mesaj_id: int, request: Request, background_tasks: BackgroundTasks, icerik: str = Form(""), db: Session = Depends(get_db)):
    try:
        cevap, hedef_idleri, konusma_id = mesaji_yanitla(db, _kullanici_id(request), mesaj_id, icerik)
    except ValueError:
        return RedirectResponse(f"/mesajlar?durum=yanit_hata#konusma-{mesaj_id}", status_code=303)
    for hedef_id in hedef_idleri:
        background_tasks.add_task(arka_planda_push_gonder, hedef_id, "Mesajınıza cevap", f"{request.session.get('kullanici_adi', 'Bir kullanıcı')} mesajınıza cevap verdi", f"/mesajlar#konusma-{konusma_id}")
    return RedirectResponse(f"/mesajlar?durum=yanitlandi#konusma-{konusma_id}", status_code=303)


@router.post("/mesajlar/{mesaj_id}/okundu")
def mesaj_okundu(mesaj_id: int, request: Request, db: Session = Depends(get_db)):
    konusma_id = mesaji_okundu_yap(db, mesaj_id, _kullanici_id(request))
    if not konusma_id:
        raise HTTPException(status_code=404, detail="Mesaj bulunamadı")
    return RedirectResponse(f"/mesajlar#konusma-{konusma_id}", status_code=303)


@router.get("/api/iletisim/ozet", response_class=JSONResponse)
def ozet(request: Request, db: Session = Depends(get_db)):
    return iletisim_ozeti(db, _kullanici_id(request))


@router.post("/api/bildirimler/okundu", response_class=JSONResponse)
def bildirim_okundu(request: Request, db: Session = Depends(get_db)):
    return {"okunan": bildirimleri_okundu_yap(db, _kullanici_id(request))}


@router.post("/mesaj-konulari/kaydet")
async def mesaj_konusu_kaydet_route(request: Request, db: Session = Depends(get_db), yetki=Depends(yetki_kontrol(ADMIN))):
    form = await request.form()
    try:
        mesaj_konusu_kaydet(db, int(form.get("konu_id")) if str(form.get("konu_id") or "").isdigit() else None, form.get("adi") or "", form.get("renk") or "primary", form.getlist("kullanici_idleri"))
    except ValueError:
        return RedirectResponse("/mesajlar?durum=konu_hata#module-konular", status_code=303)
    return RedirectResponse("/mesajlar#module-konular", status_code=303)
