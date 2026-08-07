from datetime import date

from sqlalchemy.orm import Session

from app.models.musteri import Musteri
from app.models.personel import Personel
from app.models.puantaj import Puantaj
from app.models.siparis import Siparis
from app.models.user import User
from app.models.istasyon import Istasyon
from app.models.personel_istasyon import PersonelIstasyon
from app.models.uretim_emri import UretimEmri
from app.models.uretim_kaydi import UretimKaydi
from app.models.urun import Urun
from app.models.urun_istasyon import UrunIstasyon
from app.models.uretim_plani import UretimPlanAsamasi
from app.services.puantaj_service import puantajlari_kaydet
from app.services.uretim_plan_service import planlama_verisi

SIPARIS_DURUMLARI = ("Beklemede", "Üretimde", "Sevke Hazır")


def uretim_emri_izinli_istasyonlari(db: Session, emirler: list[UretimEmri]) -> dict[int, list[int]]:
    """İş emri yalnız reçete aşamasının ya da ürün kartının istasyonlarına atanır."""
    plan_asamalari = {
        asama.id: asama.istasyon_id
        for asama in db.query(UretimPlanAsamasi).filter(
            UretimPlanAsamasi.id.in_([emir.plan_asamasi_id for emir in emirler if emir.plan_asamasi_id])
        ).all()
    }
    urun_istasyonlari: dict[int, list[int]] = {}
    for atama in db.query(UrunIstasyon).filter(
        UrunIstasyon.urun_id.in_([emir.urun_id for emir in emirler]),
        UrunIstasyon.aktif.is_(True),
    ).all():
        urun_istasyonlari.setdefault(atama.urun_id, []).append(atama.istasyon_id)
    return {
        emir.id: ([plan_asamalari[emir.plan_asamasi_id]] if emir.plan_asamasi_id in plan_asamalari else urun_istasyonlari.get(emir.urun_id, []))
        for emir in emirler
    }


def uretim_emri_istasyonunu_ata(db: Session, emir_id: int, istasyon_id: int) -> UretimEmri:
    emir = db.query(UretimEmri).filter(UretimEmri.id == emir_id, UretimEmri.aktif.is_(True)).first()
    if not emir:
        raise ValueError("Üretim emri bulunamadı")
    izinli_istasyonlar = uretim_emri_izinli_istasyonlari(db, [emir]).get(emir.id, [])
    if istasyon_id not in izinli_istasyonlar:
        raise ValueError("Bu iş emri yalnız ürün veya reçetesinde tanımlı istasyona atanabilir")
    emir.istasyon_id = istasyon_id
    db.commit()
    return emir


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
    siparisler = db.query(Siparis).filter(Siparis.aktif.is_(True)).order_by(Siparis.oncelik.asc(), Siparis.teslim_tarihi.asc(), Siparis.created_at.desc()).all()
    gruplar = {durum: [s for s in siparisler if s.durum == durum] for durum in SIPARIS_DURUMLARI}
    devamsiz_izinli_personeller = [
        {"personel": personel, "kayit": puantaj[personel.id]}
        for personel in personeller
        if personel.id in puantaj and puantaj[personel.id].durum in ("Devamsız", "Gelmedi", "İzinli")
    ]
    kullanici = db.query(User).filter(User.id == kullanici_id).first() if kullanici_id else None
    atamalar = []
    if kullanici and kullanici.personel_id:
        atamalar = db.query(PersonelIstasyon).filter(
            PersonelIstasyon.personel_id == kullanici.personel_id,
            PersonelIstasyon.aktif.is_(True),
        ).all()
    istasyon_idleri = [atama.istasyon_id for atama in atamalar]
    emir_sorgusu = db.query(UretimEmri).filter(UretimEmri.aktif.is_(True))
    if rol == "Operatör":
        emir_sorgusu = emir_sorgusu.filter(UretimEmri.istasyon_id.in_(istasyon_idleri))
    uretim_emirleri = emir_sorgusu.order_by(UretimEmri.created_at.desc()).all()
    emir_idleri = [emir.id for emir in uretim_emirleri]
    kayit_sorgusu = db.query(UretimKaydi)
    if rol == "Operatör" and kullanici:
        kayit_sorgusu = kayit_sorgusu.filter(UretimKaydi.personel_id == kullanici.personel_id)
    uretim_kayitlari = kayit_sorgusu.order_by(UretimKaydi.baslangic.desc()).limit(100).all()
    aktif_kayitlar = {kayit.uretim_emri_id: kayit for kayit in uretim_kayitlari if kayit.durum == "Devam Ediyor"}
    urunler = {u.id: u for u in db.query(Urun).filter(Urun.id.in_([e.urun_id for e in uretim_emirleri])).all()}
    istasyonlar = {i.id: i for i in db.query(Istasyon).filter(Istasyon.aktif.is_(True)).order_by(Istasyon.adi).all()}
    personel_haritasi = {p.id: p for p in db.query(Personel).all()}
    emir_haritasi = {e.id: e for e in db.query(UretimEmri).filter(UretimEmri.id.in_([k.uretim_emri_id for k in uretim_kayitlari])).all()}
    return {"personeller": personeller, "gunluk_puantaj": puantaj, "siparisler_duruma_gore": gruplar,
        "musteriler": musteriler, "aktif_siparis": len(siparisler), "uretimde": len(gruplar["Üretimde"]),
        "teslim_bekleyen": len(gruplar["Sevke Hazır"]),
        "devamsiz_izinli_personeller": devamsiz_izinli_personeller,
        "devamsiz_sayisi": len(devamsiz_izinli_personeller), "uretim_emirleri": uretim_emirleri,
        "uretim_kayitlari": uretim_kayitlari, "aktif_uretim_kayitlari": aktif_kayitlar,
        "urunler": urunler, "istasyonlar": istasyonlar, "personel_haritasi": personel_haritasi,
        "emir_haritasi": emir_haritasi, "operator_personel_id": kullanici.personel_id if kullanici else None,
        "emir_izinli_istasyonlari": uretim_emri_izinli_istasyonlari(db, uretim_emirleri),
        **planlama_verisi(db)}


def puantaj_kaydet(db: Session, secili_tarih: date, form, rol: str | None, kullanici_id: int | None) -> int:
    personeller = _gorulebilir_personeller(db, rol, kullanici_id)
    return puantajlari_kaydet(db, secili_tarih, personeller, form)
