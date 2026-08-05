from sqlalchemy.orm import Session

from app.models.firma_ayarlari import FirmaAyarlari
from app.models.islem_logu import IslemLogu
from app.models.istasyon import Istasyon
from app.models.makine import Makine
from app.models.musteri import Musteri
from app.models.personel import Personel
from app.models.urun import Urun
from app.models.urun_sinifi import UrunSinifi
from app.services.islem_log_service import islem_logla_veri


def son_excel_aktarimi(db: Session):
    return db.query(IslemLogu).filter(IslemLogu.modul == "Excel").order_by(IslemLogu.created_at.desc()).first()


def loglari_listele(db: Session, limit: int = 500):
    return db.query(IslemLogu).order_by(IslemLogu.created_at.desc()).limit(limit).all()


def firma_getir(db: Session):
    return db.query(FirmaAyarlari).first()


def firma_bilgilerini_kaydet(db: Session, kullanici_adi: str, ip_adresi: str, **alanlar):
    firma = firma_getir(db)
    if not firma:
        firma = FirmaAyarlari()
        db.add(firma)
    for alan, deger in alanlar.items():
        setattr(firma, alan, deger)
    islem_logla_veri(db, kullanici_adi, ip_adresi, "Ayarlar", "Firma bilgileri güncellendi", alanlar.get("firma_adi", ""))
    db.commit()
    return firma


def excel_sablon_verileri(db: Session):
    return {
        "firma": firma_getir(db),
        "musteriler": db.query(Musteri).order_by(Musteri.id).all(),
        "urunler": db.query(Urun).order_by(Urun.kodu).all(),
        "personeller": db.query(Personel).order_by(Personel.kodu).all(),
        "istasyonlar": db.query(Istasyon).order_by(Istasyon.kodu).all(),
        "makineler": db.query(Makine).order_by(Makine.kodu).all(),
        "siniflar": db.query(UrunSinifi).order_by(UrunSinifi.kodu).all(),
    }


def excel_indirme_logu(db: Session, kullanici_adi: str, ip_adresi: str, detay: str):
    islem_logla_veri(db, kullanici_adi, ip_adresi, "Excel", "Excel şablonu indirildi", detay, commit=True)
