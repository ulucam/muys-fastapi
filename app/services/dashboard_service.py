from datetime import date

from sqlalchemy.orm import Session

from app.models.musteri import Musteri
from app.models.personel import Personel
from app.models.puantaj import Puantaj
from app.models.siparis import Siparis
from app.models.user import User
from app.services.puantaj_service import puantajlari_kaydet

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
    devamsiz_izinli_personeller = [
        {"personel": personel, "kayit": puantaj[personel.id]}
        for personel in personeller
        if personel.id in puantaj and puantaj[personel.id].durum in ("Devamsız", "Gelmedi", "İzinli")
    ]
    return {"personeller": personeller, "gunluk_puantaj": puantaj, "siparisler_duruma_gore": gruplar,
        "musteriler": musteriler, "aktif_siparis": len(siparisler), "uretimde": len(gruplar["Üretimde"]),
        "teslim_bekleyen": len(gruplar["Sevke Hazır"]),
        "devamsiz_izinli_personeller": devamsiz_izinli_personeller,
        "devamsiz_sayisi": len(devamsiz_izinli_personeller)}


def puantaj_kaydet(db: Session, secili_tarih: date, form, rol: str | None, kullanici_id: int | None) -> int:
    personeller = _gorulebilir_personeller(db, rol, kullanici_id)
    return puantajlari_kaydet(db, secili_tarih, personeller, form)
