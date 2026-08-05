from sqlalchemy.orm import Session

from app.models.istasyon import Istasyon
from app.models.makine import Makine
from app.models.personel import Personel
from app.models.personel_makine import PersonelMakine
from app.models.puantaj import Puantaj
from app.models.recete import Recete
from app.models.recete_kalem import ReceteKalem
from app.models.urun import Urun
from app.models.urun_sinif_operasyon import UrunSinifOperasyon
from app.models.urun_sinif_operasyon_makine import UrunSinifOperasyonMakine
from app.models.urun_sinifi import UrunSinifi
from app.models.user import User

ANA_MODELLER = {"personel": Personel, "istasyon": Istasyon, "makine": Makine, "sinif": UrunSinifi}
ILISKILI_MODELLER = {"operasyon": UrunSinifOperasyon, "urun": Urun, "recete": ReceteKalem}


def ekran_verisi(db: Session, **ek) -> dict:
    atamalar = db.query(PersonelMakine).filter(PersonelMakine.aktif.is_(True)).all()
    makine_haritasi = {m.id: m for m in db.query(Makine).all()}
    personel_atamalari = {}
    for atama in atamalar:
        personel_atamalari.setdefault(atama.personel_id, []).append((atama, makine_haritasi.get(atama.makine_id)))
    personel_puantajlari = {}
    for puantaj in db.query(Puantaj).order_by(Puantaj.tarih.desc()).limit(500).all():
        if len(personel_puantajlari.setdefault(puantaj.personel_id, [])) < 10:
            personel_puantajlari[puantaj.personel_id].append(puantaj)
    data = {
        "personel_sayisi": db.query(Personel).filter(Personel.aktif.is_(True)).count(),
        "istasyon_sayisi": db.query(Istasyon).filter(Istasyon.aktif.is_(True)).count(),
        "makine_sayisi": db.query(Makine).filter(Makine.aktif.is_(True)).count(),
        "pasif_istasyon_sayisi": db.query(Istasyon).filter(Istasyon.aktif.is_(False)).count(),
        "pasif_makine_sayisi": db.query(Makine).filter(Makine.aktif.is_(False)).count(),
        "urun_sinifi_sayisi": db.query(UrunSinifi).filter(UrunSinifi.aktif.is_(True)).count(),
        "operasyon_sayisi": db.query(UrunSinifOperasyon).filter(UrunSinifOperasyon.aktif.is_(True)).count(),
        "urun_sayisi": db.query(Urun).filter(Urun.aktif.is_(True)).count(),
        "recete_bileseni_sayisi": db.query(ReceteKalem).filter(ReceteKalem.aktif.is_(True)).count(),
        "istasyonlar": db.query(Istasyon).order_by(Istasyon.kodu).all(),
        "personeller": db.query(Personel).order_by(Personel.kodu).all(),
        "makineler": db.query(Makine).order_by(Makine.kodu).all(),
        "urun_siniflari": db.query(UrunSinifi).order_by(UrunSinifi.kodu).all(),
        "urunler": db.query(Urun).order_by(Urun.kodu).all(),
        "receteler": {r.id: r for r in db.query(Recete).all()},
        "personel_atamalari": personel_atamalari,
        "personel_puantajlari": personel_puantajlari,
    }
    data.update(ek)
    return data


def personel_listesi_verisi(db: Session, q: str, departman: str, gorev: str, istasyon_id: int | None) -> dict:
    sorgu = db.query(Personel).filter(Personel.aktif.is_(True))
    if q.strip():
        arama = f"%{q.strip()}%"
        sorgu = sorgu.filter((Personel.ad_soyad.ilike(arama)) | (Personel.kodu.ilike(arama)))
    if departman: sorgu = sorgu.filter(Personel.departman == departman)
    if gorev: sorgu = sorgu.filter(Personel.gorev == gorev)
    if istasyon_id:
        makine_idleri = [m.id for m in db.query(Makine).filter(Makine.istasyon_id == istasyon_id).all()]
        personel_idleri = [a.personel_id for a in db.query(PersonelMakine).filter(PersonelMakine.makine_id.in_(makine_idleri), PersonelMakine.aktif.is_(True)).all()]
        sorgu = sorgu.filter(Personel.id.in_(personel_idleri))
    makine_haritasi = {m.id: m for m in db.query(Makine).all()}
    istasyon_haritasi = {i.id: i for i in db.query(Istasyon).all()}
    iliskiler = {}
    for atama in db.query(PersonelMakine).filter(PersonelMakine.aktif.is_(True)).all():
        makine = makine_haritasi.get(atama.makine_id)
        iliskiler.setdefault(atama.personel_id, []).append({"atama": atama, "makine": makine, "istasyon": istasyon_haritasi.get(makine.istasyon_id) if makine else None})
    return {
        "personeller": sorgu.order_by(Personel.ad_soyad).all(),
        "departmanlar": sorted({d for (d,) in db.query(Personel.departman).filter(Personel.departman != "").distinct().all()}),
        "gorevler": sorted({g for (g,) in db.query(Personel.gorev).filter(Personel.gorev != "").distinct().all()}),
        "istasyonlar": db.query(Istasyon).filter(Istasyon.aktif.is_(True)).order_by(Istasyon.kodu).all(),
        "iliskiler": iliskiler,
        "kullanici_haritasi": {u.personel_id: u for u in db.query(User).filter(User.personel_id.isnot(None)).all()},
        "istasyon_haritasi": istasyon_haritasi,
        "q": q, "departman": departman, "gorev": gorev, "istasyon_id": istasyon_id,
    }


def tanim_listesi(db: Session, goster: str):
    listeler = {
        "personeller": ("Aktif Personeller", db.query(Personel).filter(Personel.aktif.is_(True)).order_by(Personel.kodu).all()),
        "istasyonlar": ("Aktif İstasyonlar", db.query(Istasyon).filter(Istasyon.aktif.is_(True)).order_by(Istasyon.kodu).all()),
        "makineler": ("Aktif Makineler", db.query(Makine).filter(Makine.aktif.is_(True)).order_by(Makine.kodu).all()),
        "istasyonlar_pasif": ("Pasif İstasyonlar", db.query(Istasyon).filter(Istasyon.aktif.is_(False)).order_by(Istasyon.kodu).all()),
        "makineler_pasif": ("Pasif Makineler", db.query(Makine).filter(Makine.aktif.is_(False)).order_by(Makine.kodu).all()),
        "urun_siniflari": ("Aktif Ürün Sınıfları", db.query(UrunSinifi).filter(UrunSinifi.aktif.is_(True)).order_by(UrunSinifi.kodu).all()),
        "operasyonlar": ("Sınıf Reçetesi Operasyonları", db.query(UrunSinifOperasyon).order_by(UrunSinifOperasyon.urun_sinifi_id, UrunSinifOperasyon.sira_no).all()),
        "urunler": ("Ürün Kartları", db.query(Urun).order_by(Urun.kodu).all()),
        "recete_bilesenleri": ("Ürün Reçetesi Bileşenleri", db.query(ReceteKalem).order_by(ReceteKalem.recete_id, ReceteKalem.sira_no).all()),
    }
    return listeler.get(goster, (None, []))


def personel_puantaji(db: Session, personel_id: int):
    personel = db.query(Personel).filter(Personel.id == personel_id).first()
    puantajlar = db.query(Puantaj).filter(Puantaj.personel_id == personel_id).order_by(Puantaj.tarih.desc()).all() if personel else []
    return personel, puantajlar


def ana_kayit_getir(db: Session, tip: str, kod: str):
    model = ANA_MODELLER.get(tip)
    return db.query(model).filter(model.kodu == kod).first() if model else None


def iliskili_kayit_getir(db: Session, tip: str, kayit_id: int):
    model = ILISKILI_MODELLER.get(tip)
    kayit = db.query(model).filter(model.id == kayit_id).first() if model else None
    makine_idleri = [x.makine_id for x in db.query(UrunSinifOperasyonMakine).filter(UrunSinifOperasyonMakine.operasyon_id == kayit_id).all()] if tip == "operasyon" else []
    return kayit, makine_idleri


def tanim_sil(db: Session, tip: str, kod: str) -> bool:
    model = {"istasyon": Istasyon, "makine": Makine}.get(tip)
    kayit = db.query(model).filter(model.kodu == kod).first() if model else None
    if not kayit: return False
    try:
        db.delete(kayit); db.commit()
    except Exception:
        db.rollback(); kayit = db.query(model).filter(model.kodu == kod).first()
        if kayit: kayit.aktif = False; db.commit()
    return True
