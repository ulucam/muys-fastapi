from sqlalchemy.orm import Session

from app.models.recete import Recete
from app.models.urun import Urun
from app.models.stok_urun_sinifi import StokUrunSinifi
from app.models.stok_urun_turu import StokUrunTuru


def stok_urunlerini_listele(db: Session):
    return db.query(Urun).order_by(Urun.adi).all()


def hammaddeleri_listele(db: Session):
    return db.query(Urun).order_by(Urun.kodu).all()


def stok_tanimlari(db: Session):
    return (db.query(StokUrunTuru).filter(StokUrunTuru.aktif.is_(True)).order_by(StokUrunTuru.adi).all(),
            db.query(StokUrunSinifi).filter(StokUrunSinifi.aktif.is_(True)).order_by(StokUrunSinifi.adi).all())


def stok_urunu_kaydet(db: Session, kodu: str, adi: str, tur_id: int, sinif_id: int | None, birim: str):
    tur = db.query(StokUrunTuru).filter(StokUrunTuru.id == tur_id, StokUrunTuru.aktif.is_(True)).first()
    sinif = db.query(StokUrunSinifi).filter(StokUrunSinifi.id == sinif_id, StokUrunSinifi.aktif.is_(True)).first() if sinif_id else None
    if not kodu.strip() or not adi.strip() or not tur or (sinif_id and not sinif):
        raise ValueError("Ürün kodu, adı ve geçerli tür zorunludur")
    urun = db.query(Urun).filter(Urun.kodu == kodu.strip()).first() or Urun(kodu=kodu.strip())
    urun.adi, urun.stok_urun_turu_id, urun.stok_urun_sinifi_id = adi.strip(), tur.id, sinif.id if sinif else None
    urun.urun_tipi, urun.birim, urun.aktif = ("Mamul" if tur.uretilen else "Hammadde"), birim.strip() or "Adet", True
    db.add(urun); db.commit()
    return urun


def receteleri_listele(db: Session):
    return db.query(Recete).order_by(Recete.id.desc()).all()
