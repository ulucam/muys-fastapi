from sqlalchemy.orm import Session

from app.models.urun import Urun


def urunleri_listele(db: Session):
    return db.query(Urun).order_by(Urun.adi).all()


def urun_olustur(db: Session, urun_data) -> Urun | None:
    if db.query(Urun).filter(Urun.kodu == urun_data.kodu).first():
        return None
    urun = Urun(**urun_data.model_dump())
    db.add(urun)
    db.commit()
    db.refresh(urun)
    return urun
