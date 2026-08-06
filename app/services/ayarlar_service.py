from pathlib import Path
from uuid import uuid4

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


def firma_adi_getir(db: Session) -> str:
    firma = firma_getir(db)
    return firma.firma_adi if firma and firma.firma_adi else "MÜYS"


def firma_ozeti_getir(db: Session) -> tuple[str, str]:
    firma = firma_getir(db)
    if not firma:
        return "MÜYS", ""
    return firma.firma_adi or "MÜYS", firma.logo_yolu or ""


def _logo_dosyasini_kaydet(logo_dosyasi: tuple[str, bytes]) -> str:
    dosya_adi, icerik = logo_dosyasi
    if not icerik:
        raise ValueError("Logo dosyası boş olamaz")
    if len(icerik) > 3 * 1024 * 1024:
        raise ValueError("Logo dosyası en fazla 3 MB olabilir")
    uzanti = Path(dosya_adi).suffix.lower()
    imza_uzantilari = {
        b"\x89PNG\r\n\x1a\n": ".png",
        b"\xff\xd8\xff": ".jpg",
        b"GIF87a": ".gif",
        b"GIF89a": ".gif",
    }
    gercek_uzanti = next((deger for imza, deger in imza_uzantilari.items() if icerik.startswith(imza)), None)
    if icerik.startswith(b"RIFF") and icerik[8:12] == b"WEBP":
        gercek_uzanti = ".webp"
    if not gercek_uzanti or uzanti not in {".png", ".jpg", ".jpeg", ".gif", ".webp"}:
        raise ValueError("Logo yalnızca PNG, JPG, GIF veya WEBP biçiminde olmalıdır")
    klasor = Path("app/static/uploads/logolar")
    klasor.mkdir(parents=True, exist_ok=True)
    kayit_adi = f"firma-logo-{uuid4().hex}{gercek_uzanti}"
    (klasor / kayit_adi).write_bytes(icerik)
    return f"/static/uploads/logolar/{kayit_adi}"


def firma_bilgilerini_kaydet(db: Session, kullanici_adi: str, ip_adresi: str, logo_dosyasi: tuple[str, bytes] | None = None, **alanlar):
    firma = firma_getir(db)
    if not firma:
        firma = FirmaAyarlari()
        db.add(firma)
    for alan, deger in alanlar.items():
        setattr(firma, alan, deger)
    if logo_dosyasi:
        firma.logo_yolu = _logo_dosyasini_kaydet(logo_dosyasi)
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
