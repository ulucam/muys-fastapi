from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.context import template_data
from app.database import get_db
from app.services.dashboard_service import (
    dashboard_verisi,
    puantaj_kaydet as puantaj_kaydet_service,
)
from app.services.islem_log_service import islem_logla
from app.models.user import User
from app.models.personel_istasyon import PersonelIstasyon
from app.models.uretim_emri import UretimEmri
from app.models.uretim_kaydi import UretimKaydi
from app.models.urun import Urun
from app.models.istasyon import Istasyon
from app.models.personel import Personel
from app.models.siparis import Siparis
from app.models.uretim_plani import UretimPlani, UretimPlanAsamasi
from app.services.uretim_plan_service import plan_asamasini_tamamla, uretim_plani_olustur

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def tarihi_oku(deger: str | None) -> date:
    try:
        return datetime.strptime(deger or "", "%Y-%m-%d").date()
    except ValueError:
        return date.today()


def _operator_bilgisi(request: Request, db: Session) -> User:
    kullanici = db.query(User).filter(User.id == request.session.get("user_id")).first()
    if not kullanici or kullanici.rol not in ("Operatör", "OperatÃ¶r") or not kullanici.personel_id:
        raise HTTPException(status_code=403, detail="Bu işlem yalnızca personele bağlı operatör hesabıyla yapılabilir.")
    return kullanici


def _emir_operator_icin_uygun(db: Session, personel_id: int, emir_id: int) -> UretimEmri:
    emir = db.query(UretimEmri).filter(UretimEmri.id == emir_id, UretimEmri.aktif.is_(True)).first()
    if not emir or not emir.istasyon_id:
        raise HTTPException(status_code=404, detail="Atanmış üretim emri bulunamadı.")
    atama = db.query(PersonelIstasyon).filter(
        PersonelIstasyon.personel_id == personel_id,
        PersonelIstasyon.istasyon_id == emir.istasyon_id,
        PersonelIstasyon.aktif.is_(True),
    ).first()
    if not atama:
        raise HTTPException(status_code=403, detail="Bu emir sizin istasyonunuza ait değil.")
    return emir


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


@router.post("/uretim/{emir_id}/baslat")
def uretim_baslat(emir_id: int, request: Request, db: Session = Depends(get_db)):
    kullanici = _operator_bilgisi(request, db)
    emir = _emir_operator_icin_uygun(db, kullanici.personel_id, emir_id)
    devam_eden = db.query(UretimKaydi).filter(
        UretimKaydi.personel_id == kullanici.personel_id,
        UretimKaydi.durum == "Devam Ediyor",
    ).first()
    if devam_eden:
        raise HTTPException(status_code=409, detail="Bitirilmemiş bir işiniz zaten var.")
    db.add(UretimKaydi(
        uretim_emri_id=emir.id, personel_id=kullanici.personel_id,
        istasyon_id=emir.istasyon_id, baslangic=datetime.now(), durum="Devam Ediyor",
    ))
    emir.durum = "Üretimde"
    if not emir.baslama_tarihi:
        emir.baslama_tarihi = datetime.now()
    if emir.plan_asamasi_id:
        plan_asamasi = db.query(UretimPlanAsamasi).filter(UretimPlanAsamasi.id == emir.plan_asamasi_id).first()
        if plan_asamasi:
            plan_asamasi.durum = "Üretimde"
            if not plan_asamasi.baslama_tarihi:
                plan_asamasi.baslama_tarihi = datetime.now()
    if emir.uretim_plani_id:
        plan = db.query(UretimPlani).filter(UretimPlani.id == emir.uretim_plani_id).first()
        if plan:
            plan.durum = "Üretimde"
    db.commit()
    return RedirectResponse("/?uretim=basladi#uretim-paneli", status_code=303)


@router.post("/uretim/{kayit_id}/bitir")
async def uretim_bitir(kayit_id: int, request: Request, db: Session = Depends(get_db)):
    kullanici = _operator_bilgisi(request, db)
    kayit = db.query(UretimKaydi).filter(
        UretimKaydi.id == kayit_id, UretimKaydi.personel_id == kullanici.personel_id,
        UretimKaydi.durum == "Devam Ediyor",
    ).first()
    if not kayit:
        raise HTTPException(status_code=404, detail="Devam eden üretim kaydı bulunamadı.")
    form = await request.form()
    try:
        miktar = float(form.get("uretilen_miktar") or 0)
        fire = float(form.get("fire_miktari") or 0)
    except (TypeError, ValueError):
        raise HTTPException(status_code=422, detail="Miktar alanları sayı olmalıdır.")
    if miktar < 0 or fire < 0 or miktar + fire <= 0:
        raise HTTPException(status_code=422, detail="Üretim veya fire miktarı girilmelidir.")
    kayit.uretilen_miktar, kayit.fire_miktari = miktar, fire
    kayit.aciklama = (form.get("aciklama") or "").strip()[:500]
    kayit.bitis, kayit.durum = datetime.now(), "Tamamlandı"
    emir = db.query(UretimEmri).filter(UretimEmri.id == kayit.uretim_emri_id).first()
    if emir:
        toplam = sum(k.uretilen_miktar or 0 for k in db.query(UretimKaydi).filter(UretimKaydi.uretim_emri_id == emir.id).all())
        if toplam >= emir.miktar:
            emir.durum, emir.bitis_tarihi = "Tamamlandı", datetime.now()
            emir.aktif = False
            plan_asamasini_tamamla(db, emir, toplam, sum(k.fire_miktari or 0 for k in db.query(UretimKaydi).filter(UretimKaydi.uretim_emri_id == emir.id).all()))
    db.commit()
    return RedirectResponse("/?uretim=tamamlandi#uretim-paneli", status_code=303)


@router.post("/uretim/planla")
async def uretim_planla(request: Request, db: Session = Depends(get_db)):
    if request.session.get("rol") not in ("Admin", "Üretim", "Ãœretim"):
        raise HTTPException(status_code=403, detail="Üretim planlama yetkiniz yok.")
    form = await request.form()
    try:
        uretim_plani_olustur(db, int(form.get("recete_id") or 0), float(form.get("miktar") or 0),
            form.get("hedef_turu") or "", int(form.get("siparis_kalem_id")) if str(form.get("siparis_kalem_id") or "").isdigit() else None,
            form.get("aciklama") or "")
    except (ValueError, TypeError):
        return RedirectResponse("/?plan=hata#dashboard-uretim", status_code=303)
    return RedirectResponse("/?plan=hazir#dashboard-uretim", status_code=303)


@router.post("/uretim/{emir_id}/istasyon")
async def uretim_istasyon_ata(emir_id: int, request: Request, db: Session = Depends(get_db)):
    if request.session.get("rol") not in ("Admin", "Üretim", "Ãœretim"):
        raise HTTPException(status_code=403, detail="İstasyon atamasını yalnızca üretim yönetimi yapabilir.")
    form = await request.form()
    emir = db.query(UretimEmri).filter(UretimEmri.id == emir_id).first()
    istasyon = db.query(Istasyon).filter(Istasyon.id == int(form.get("istasyon_id") or 0), Istasyon.aktif.is_(True)).first()
    if not emir or not istasyon:
        raise HTTPException(status_code=404, detail="Emir veya istasyon bulunamadı.")
    emir.istasyon_id = istasyon.id
    db.commit()
    return RedirectResponse("/?istasyon=atandi#uretim-emirleri", status_code=303)


@router.post("/siparis/{siparis_id}/onay")
async def siparis_onayla(siparis_id: int, request: Request, db: Session = Depends(get_db)):
    if request.session.get("rol") not in ("Admin", "Patron"):
        raise HTTPException(status_code=403, detail="Sipariş onaylama yetkiniz yok.")
    form = await request.form()
    siparis = db.query(Siparis).filter(Siparis.id == siparis_id, Siparis.aktif.is_(True)).first()
    if not siparis:
        raise HTTPException(status_code=404, detail="Sipariş bulunamadı.")
    karar = form.get("karar")
    if karar not in ("Onaylandı", "Reddedildi"):
        raise HTTPException(status_code=422, detail="Geçersiz onay kararı.")
    siparis.onay_durumu = karar
    siparis.onay_tarihi = datetime.now()
    siparis.onaylayan_kullanici_id = request.session.get("user_id")
    db.commit()
    return RedirectResponse("/?siparis_onay=1#siparis-onay", status_code=303)


@router.post("/siparis/{siparis_id}/oncelik")
async def siparis_oncelik(siparis_id: int, request: Request, db: Session = Depends(get_db)):
    if request.session.get("rol") not in ("Admin", "Patron"):
        raise HTTPException(status_code=403, detail="Sipariş sıralama yetkiniz yok.")
    form = await request.form()
    siparis = db.query(Siparis).filter(Siparis.id == siparis_id, Siparis.aktif.is_(True)).first()
    try:
        oncelik = int(form.get("oncelik") or 100)
    except (TypeError, ValueError):
        raise HTTPException(status_code=422, detail="Sıra sayı olmalıdır.")
    if not siparis or not 1 <= oncelik <= 999:
        raise HTTPException(status_code=422, detail="Sıra 1-999 arasında olmalıdır.")
    siparis.oncelik = oncelik
    db.commit()
    return RedirectResponse("/?siparis_sira=1#siparis-onay", status_code=303)


@router.get("/api/dashboard/uretim-durum", response_class=JSONResponse)
def uretim_durum(request: Request, db: Session = Depends(get_db)):
    if not request.session.get("user_id"):
        raise HTTPException(status_code=401, detail="Oturum gerekli.")
    kayitlar = db.query(UretimKaydi).order_by(UretimKaydi.baslangic.desc()).limit(100).all()
    emirler = {e.id: e for e in db.query(UretimEmri).filter(UretimEmri.id.in_([k.uretim_emri_id for k in kayitlar])).all()}
    urunler = {u.id: u for u in db.query(Urun).filter(Urun.id.in_([e.urun_id for e in emirler.values()])).all()}
    istasyonlar = {i.id: i for i in db.query(Istasyon).all()}
    personeller = {p.id: p for p in db.query(Personel).all()}
    simdi = datetime.now()
    return [{
        "id": k.id, "emir_no": emirler[k.uretim_emri_id].emir_no if k.uretim_emri_id in emirler else "-",
        "urun": urunler[emirler[k.uretim_emri_id].urun_id].adi if k.uretim_emri_id in emirler and emirler[k.uretim_emri_id].urun_id in urunler else "-",
        "operasyon": emirler[k.uretim_emri_id].aciklama if k.uretim_emri_id in emirler else "",
        "operator": personeller[k.personel_id].ad_soyad if k.personel_id in personeller else "-",
        "istasyon": istasyonlar[k.istasyon_id].adi if k.istasyon_id in istasyonlar else "-",
        "durum": k.durum, "baslangic": k.baslangic.strftime("%d.%m.%Y %H:%M"),
        "bitis": k.bitis.strftime("%d.%m.%Y %H:%M") if k.bitis else "-",
        "sure_dakika": int(((k.bitis or simdi) - k.baslangic).total_seconds() / 60),
        "uretilen_miktar": k.uretilen_miktar or 0, "fire_miktari": k.fire_miktari or 0,
    } for k in kayitlar]


@router.post("/puantaj/kaydet")
async def puantaj_kaydet(request: Request, db: Session = Depends(get_db)):
    if request.session.get("rol") in ("Operatör", "Patron"):
        raise HTTPException(status_code=403, detail="Bu rol puantaj kayıtlarını yalnızca görüntüleyebilir.")
    form = await request.form()
    secili_tarih = tarihi_oku(form.get("tarih"))
    personel_sayisi = puantaj_kaydet_service(db, secili_tarih, form, request.session.get("rol"), request.session.get("user_id"))
    islem_logla(db, request, "Puantaj", "Günlük puantaj kaydedildi", f"Tarih: {secili_tarih.isoformat()}, personel: {personel_sayisi}", commit=True)
    return RedirectResponse(f"/?tarih={secili_tarih.isoformat()}&puantaj=1#puantaj", status_code=303)
