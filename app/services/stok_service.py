from sqlalchemy.orm import Session

from app.models.recete import Recete
from app.models.urun import Urun
from app.models.stok_urun_sinifi import StokUrunSinifi
from app.models.stok_urun_turu import StokUrunTuru


def stok_urunlerini_listele(db: Session):
    return db.query(Urun).order_by(Urun.adi).all()


def hammaddeleri_listele(db: Session):
    return (
        db.query(Urun)
        .join(StokUrunTuru, StokUrunTuru.id == Urun.stok_urun_turu_id)
        .filter(StokUrunTuru.uretilen.is_(False))
        .order_by(Urun.kodu)
        .all()
    )


def stok_tanimlari(db: Session):
    return (
        db.query(StokUrunTuru).filter(StokUrunTuru.uretilen.is_(False)).order_by(StokUrunTuru.adi).all(),
        db.query(StokUrunSinifi).order_by(StokUrunSinifi.adi).all(),
    )


def stok_tum_tanimlari(db: Session):
    return (
        db.query(StokUrunTuru).order_by(StokUrunTuru.adi).all(),
        db.query(StokUrunSinifi).order_by(StokUrunSinifi.adi).all(),
    )


def stok_kurulum_durumu(db: Session) -> dict:
    tur_sayisi = db.query(StokUrunTuru).filter(StokUrunTuru.aktif.is_(True), StokUrunTuru.uretilen.is_(False)).count()
    sinif_sayisi = db.query(StokUrunSinifi).filter(StokUrunSinifi.aktif.is_(True)).count()
    hammadde_sayisi = (
        db.query(Urun)
        .join(StokUrunTuru, StokUrunTuru.id == Urun.stok_urun_turu_id)
        .filter(Urun.aktif.is_(True), StokUrunTuru.uretilen.is_(False))
        .count()
    )
    return {
        "turler_hazir": tur_sayisi > 0,
        "siniflar_hazir": sinif_sayisi > 0,
        "hammadde_hazir": hammadde_sayisi > 0,
        "hammadde_eklenebilir": tur_sayisi > 0 and sinif_sayisi > 0,
        "yari_mamul_eklenebilir": hammadde_sayisi > 0,
    }


def stok_urunu_kaydet(
    db: Session, kodu: str, adi: str, tur_id: int, sinif_id: int | None,
    birim: str, marka: str = "", model: str = "", mevcut_stok: float = 0,
    min_stok: float = 0, urun_id: int | None = None,
):
    tur = db.query(StokUrunTuru).filter(StokUrunTuru.id == tur_id, StokUrunTuru.aktif.is_(True), StokUrunTuru.uretilen.is_(False)).first()
    sinif = db.query(StokUrunSinifi).filter(StokUrunSinifi.id == sinif_id, StokUrunSinifi.aktif.is_(True)).first() if sinif_id else None
    if db.query(StokUrunSinifi).filter(StokUrunSinifi.aktif.is_(True)).count() == 0:
        raise ValueError("Hammadde kartından önce en az bir takip sınıfı tanımlanmalıdır")
    if not kodu.strip() or not adi.strip() or not tur or (sinif_id and not sinif):
        raise ValueError("Ürün kodu, adı ve geçerli tür zorunludur")
    urun = db.query(Urun).filter(Urun.id == urun_id).first() if urun_id else None
    kod_cakismasi = db.query(Urun).filter(Urun.kodu == kodu.strip(), Urun.id != (urun.id if urun else 0)).first()
    if kod_cakismasi:
        raise ValueError("Bu stok kodu başka bir üründe kullanılıyor")
    urun = urun or Urun(kodu=kodu.strip())
    urun.kodu = kodu.strip()
    urun.adi, urun.stok_urun_turu_id, urun.stok_urun_sinifi_id = adi.strip(), tur.id, sinif.id if sinif else None
    urun.urun_tipi, urun.birim, urun.aktif = ("YariMamul" if tur.uretilen else "Hammadde"), birim.strip() or "Adet", True
    urun.marka, urun.model = marka.strip(), model.strip()
    urun.mevcut_stok, urun.min_stok = mevcut_stok, min_stok
    db.add(urun); db.commit()
    return urun


def stok_turu_kaydet(db: Session, adi: str, tur_id: int | None = None):
    temiz_ad = adi.strip()
    tur = db.query(StokUrunTuru).filter(StokUrunTuru.id == tur_id, StokUrunTuru.uretilen.is_(False)).first() if tur_id else None
    cakisan = db.query(StokUrunTuru).filter(StokUrunTuru.adi == temiz_ad, StokUrunTuru.id != (tur.id if tur else 0)).first()
    if not temiz_ad or cakisan:
        raise ValueError("Tür adı zorunludur ve benzersiz olmalıdır")
    tur = tur or StokUrunTuru(uretilen=False)
    tur.adi, tur.aktif = temiz_ad, True
    db.add(tur); db.commit()
    return tur


def stok_sinifi_kaydet(db: Session, adi: str, sinif_id: int | None = None):
    temiz_ad = adi.strip()
    sinif = db.query(StokUrunSinifi).filter(StokUrunSinifi.id == sinif_id).first() if sinif_id else None
    cakisan = db.query(StokUrunSinifi).filter(StokUrunSinifi.adi == temiz_ad, StokUrunSinifi.id != (sinif.id if sinif else 0)).first()
    if not temiz_ad or cakisan:
        raise ValueError("Sınıf adı zorunludur ve benzersiz olmalıdır")
    sinif = sinif or StokUrunSinifi()
    sinif.adi, sinif.aktif = temiz_ad, True
    db.add(sinif); db.commit()
    return sinif


def receteleri_listele(db: Session):
    return db.query(Recete).order_by(Recete.id.desc()).all()
