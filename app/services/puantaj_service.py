from sqlalchemy.orm import Session

from app.models.personel import Personel
from app.models.puantaj import Puantaj


PUANTAJ_DURUMLARI = ("Geldi", "Gelmedi", "İzinli", "Raporlu")
DEVAMSIZ_DURUMLARI = ("Gelmedi", "Devamsız")


def puantaj_listesi_verisi(db: Session, tarih, sadece_gelmeyen: bool = False) -> dict:
    personeller = db.query(Personel).filter(Personel.aktif.is_(True)).order_by(Personel.ad_soyad).all()
    kayitlar = {
        kayit.personel_id: kayit
        for kayit in db.query(Puantaj).filter(Puantaj.tarih == tarih).all()
    }
    if sadece_gelmeyen:
        personeller = [
            personel for personel in personeller
            if kayitlar.get(personel.id) and kayitlar[personel.id].durum in DEVAMSIZ_DURUMLARI
        ]
    return {
        "puantaj_personelleri": personeller,
        "puantaj_kayitlari": kayitlar,
        "puantaj_tarihi": tarih,
        "sadece_gelmeyen": sadece_gelmeyen,
    }


def puantajlari_kaydet(db: Session, tarih, personeller: list[Personel], form) -> int:
    personel_idleri = [personel.id for personel in personeller]
    mevcutlar = {
        kayit.personel_id: kayit
        for kayit in db.query(Puantaj).filter(
            Puantaj.tarih == tarih,
            Puantaj.personel_id.in_(personel_idleri),
        ).all()
    }
    for personel in personeller:
        durum = str(form.get(f"durum_{personel.id}") or "Geldi")
        durum = durum if durum in PUANTAJ_DURUMLARI else "Geldi"
        kayit = mevcutlar.get(personel.id)
        if not kayit:
            kayit = Puantaj(personel_id=personel.id, tarih=tarih)
            db.add(kayit)
        kayit.durum = durum
        kayit.aciklama = str(form.get(f"aciklama_{personel.id}") or "").strip()
    return len(personeller)


def puantaj_kayitlarini_guncelle(db: Session, tarih, form) -> int:
    """Personeller ekranında yalnızca gönderilen aktif personelleri günceller."""
    personel_idleri = {
        int(deger)
        for deger in form.getlist("personel_idleri")
        if str(deger).isdigit()
    }
    personeller = (
        db.query(Personel)
        .filter(Personel.id.in_(personel_idleri), Personel.aktif.is_(True))
        .order_by(Personel.ad_soyad)
        .all()
        if personel_idleri else []
    )
    return puantajlari_kaydet(db, tarih, personeller, form)


def personel_puantaji(db: Session, personel_id: int):
    personel = db.query(Personel).filter(Personel.id == personel_id).first()
    puantajlar = (
        db.query(Puantaj)
        .filter(Puantaj.personel_id == personel_id)
        .order_by(Puantaj.tarih.desc())
        .all()
        if personel else []
    )
    return personel, puantajlar
