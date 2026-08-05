from sqlalchemy.orm import Session

from app.models.recete import Recete
from app.models.urun import Urun


def stok_urunlerini_listele(db: Session):
    return db.query(Urun).order_by(Urun.adi).all()


def hammaddeleri_listele(db: Session):
    return db.query(Urun).filter(Urun.urun_tipi == "Hammadde").order_by(Urun.kodu).all()


def receteleri_listele(db: Session):
    return db.query(Recete).order_by(Recete.id.desc()).all()
