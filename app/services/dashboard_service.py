from datetime import date

from sqlalchemy.orm import Session

from app.models.musteri import Musteri
from app.models.personel import Personel
from app.models.puantaj import Puantaj
from app.models.siparis import Siparis
from app.models.user import User

PUANTAJ_DURUMLARI = ("Geldi", "Gelmedi", "İzinli", "Raporlu")
SIPARIS_DURUMLARI = ("Beklemede", "Üretimde", "Sevke Hazır")


def _gorulebilir_personeller(db: Session, rol: str | None, kullanici_id: int | None):
    sorgu = db.query(Personel).filter(Personel.aktif.is_(True))
    if rol == "Operatör":
        kullanici = db.query(User).filter(User.id == kullanici_id).first()
        sorgu = sorgu.filter(Personel.id == (kullanici.personel_id if kullanici else None))
    return sorgu.order_by(Personel.ad_soyad).all()


def dashboard_verisi(db: Session, secili_tarih: date, rol: str | None, kullanici_id: int | None) -> dict:
    personeller = _gorulebilir_personeller(db, rol, kullanici_id)
    personel_idleri = [personel.id for personel in personeller]
    puantaj = {p.personel_id: p for p in db.query(Puantaj).filter(Puantaj.tarih == secili_tarih, Puantaj.personel_id.in_(personel_idleri)).all()}
    musteriler = {m.id: m for m in db.query(Musteri).all()}
    siparisler = db.query(Siparis).filter(Siparis.aktif.is_(True)).order_by(Siparis.teslim_tarihi.asc(), Siparis.created_at.desc()).all()
    gruplar = {durum: [s for s in siparisler if s.durum == durum] for durum in SIPARIS_DURUMLARI}
    return {"personeller": personeller, "gunluk_puantaj": puantaj, "siparisler_duruma_gore": gruplar,
        "musteriler": musteriler, "aktif_siparis": len(siparisler), "uretimde": len(gruplar["Üretimde"]),
        "teslim_bekleyen": len(gruplar["Sevke Hazır"]),
        "devamsiz_sayisi": sum(1 for p in puantaj.values() if p.durum in ("Devamsız", "Gelmedi"))}


def puantaj_kaydet(db: Session, secili_tarih: date, form, rol: str | None, kullanici_id: int | None) -> int:
    personeller = _gorulebilir_personeller(db, rol, kullanici_id)
    mevcutlar = {p.personel_id: p for p in db.query(Puantaj).filter(Puantaj.tarih == secili_tarih).all()}
    for personel in personeller:
        durum = str(form.get(f"durum_{personel.id}") or "Geldi")
        durum = durum if durum in PUANTAJ_DURUMLARI else "Geldi"
        kayit = mevcutlar.get(personel.id)
        if not kayit:
            kayit = Puantaj(personel_id=personel.id, tarih=secili_tarih)
            db.add(kayit)
        kayit.durum = durum
        kayit.aciklama = str(form.get(f"aciklama_{personel.id}") or "").strip()
    return len(personeller)
