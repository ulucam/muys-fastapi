from datetime import date, datetime

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.context import template_data
from app.database import get_db
from app.models.musteri import Musteri
from app.models.personel import Personel
from app.models.puantaj import Puantaj
from app.models.siparis import Siparis
from app.services.islem_log_service import islem_logla

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
PUANTAJ_DURUMLARI = ("Geldi", "Devamsız", "İzinli", "Raporlu")
SIPARIS_DURUMLARI = ("Beklemede", "Üretimde", "Sevke Hazır")


def tarihi_oku(deger: str | None) -> date:
    try:
        return datetime.strptime(deger or "", "%Y-%m-%d").date()
    except ValueError:
        return date.today()


@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request, tarih: str | None = None, db: Session = Depends(get_db)):
    secili_tarih = tarihi_oku(tarih)
    personeller = db.query(Personel).filter(Personel.aktif.is_(True)).order_by(Personel.ad_soyad).all()
    gunluk_puantaj = {
        p.personel_id: p
        for p in db.query(Puantaj).filter(Puantaj.tarih == secili_tarih).all()
    }
    musteriler = {m.id: m for m in db.query(Musteri).all()}
    siparisler = db.query(Siparis).filter(Siparis.aktif.is_(True)).order_by(
        Siparis.teslim_tarihi.asc(), Siparis.created_at.desc()
    ).all()
    siparisler_duruma_gore = {
        durum: [s for s in siparisler if s.durum == durum] for durum in SIPARIS_DURUMLARI
    }
    data = template_data(request)
    data.update({
        "secili_tarih": secili_tarih,
        "bugun": date.today(),
        "personeller": personeller,
        "gunluk_puantaj": gunluk_puantaj,
        "puantaj_durumlari": PUANTAJ_DURUMLARI,
        "siparisler_duruma_gore": siparisler_duruma_gore,
        "musteriler": musteriler,
        "aktif_siparis": len(siparisler),
        "uretimde": len(siparisler_duruma_gore["Üretimde"]),
        "teslim_bekleyen": len(siparisler_duruma_gore["Sevke Hazır"]),
        "devamsiz_sayisi": sum(1 for p in gunluk_puantaj.values() if p.durum == "Devamsız"),
    })
    return templates.TemplateResponse("dashboard/index.html", data)


@router.post("/puantaj/kaydet")
async def puantaj_kaydet(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    secili_tarih = tarihi_oku(form.get("tarih"))
    aktif_personeller = db.query(Personel).filter(Personel.aktif.is_(True)).all()
    mevcutlar = {
        p.personel_id: p
        for p in db.query(Puantaj).filter(Puantaj.tarih == secili_tarih).all()
    }
    for personel in aktif_personeller:
        durum = str(form.get(f"durum_{personel.id}") or "Geldi")
        if durum not in PUANTAJ_DURUMLARI:
            durum = "Geldi"
        kayit = mevcutlar.get(personel.id)
        if not kayit:
            kayit = Puantaj(personel_id=personel.id, tarih=secili_tarih)
            db.add(kayit)
        kayit.durum = durum
        kayit.aciklama = str(form.get(f"aciklama_{personel.id}") or "").strip()
    islem_logla(db, request, "Puantaj", "Günlük puantaj kaydedildi", f"Tarih: {secili_tarih.isoformat()}, personel: {len(aktif_personeller)}")
    db.commit()
    return RedirectResponse(f"/?tarih={secili_tarih.isoformat()}#puantaj", status_code=303)
