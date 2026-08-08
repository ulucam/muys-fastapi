from datetime import datetime
from io import BytesIO
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from sqlalchemy import MetaData, select
from sqlalchemy.orm import Session

from app.models.firma_ayarlari import FirmaAyarlari
from app.models.islem_logu import IslemLogu
from app.models.istasyon import Istasyon
from app.models.makine import Makine
from app.models.musteri import Musteri
from app.models.personel import Personel
from app.models.personel_istasyon import PersonelIstasyon
from app.models.urun import Urun
from app.models.urun_sinifi import UrunSinifi
from app.models.stok_urun_sinifi import StokUrunSinifi
from app.models.stok_urun_turu import StokUrunTuru
from app.models.urun_istasyon import UrunIstasyon
from app.services.islem_log_service import islem_logla_veri


def son_excel_aktarimi(db: Session):
    return db.query(IslemLogu).filter(IslemLogu.modul == "Excel").order_by(IslemLogu.created_at.desc()).first()


def loglari_listele(
    db: Session, sayfa: int = 1, sayfa_basina: int = 50, kullanici_adi: str = "",
    modul: str = "", islem: str = "",
) -> dict:
    sorgu = db.query(IslemLogu)
    if kullanici_adi:
        sorgu = sorgu.filter(IslemLogu.kullanici_adi == kullanici_adi)
    if modul:
        sorgu = sorgu.filter(IslemLogu.modul == modul)
    if islem:
        sorgu = sorgu.filter(IslemLogu.islem == islem)
    toplam_kayit = sorgu.count()
    sayfa_sayisi = max(1, (toplam_kayit + sayfa_basina - 1) // sayfa_basina)
    sayfa = min(max(1, sayfa), sayfa_sayisi)
    loglar = (
        sorgu
        .order_by(IslemLogu.created_at.desc())
        .offset((sayfa - 1) * sayfa_basina)
        .limit(sayfa_basina)
        .all()
    )
    return {
        "loglar": loglar,
        "log_sayfasi": sayfa,
        "log_sayfa_sayisi": sayfa_sayisi,
        "log_toplam_kayit": toplam_kayit,
        "log_kullanici_secimleri": [deger for (deger,) in db.query(IslemLogu.kullanici_adi).distinct().order_by(IslemLogu.kullanici_adi).all()],
        "log_modul_secimleri": [deger for (deger,) in db.query(IslemLogu.modul).distinct().order_by(IslemLogu.modul).all()],
        "log_islem_secimleri": [deger for (deger,) in db.query(IslemLogu.islem).distinct().order_by(IslemLogu.islem).all()],
        "secili_log_kullanicisi": kullanici_adi,
        "secili_log_modulu": modul,
        "secili_log_islemi": islem,
    }


def firma_getir(db: Session):
    return db.query(FirmaAyarlari).first()


def sistem_ayarlari_getir(db: Session) -> FirmaAyarlari:
    """Sistem ayarlarını firma ayarlarıyla aynı tekil kayıtta tutar."""
    ayarlar = firma_getir(db)
    if not ayarlar:
        ayarlar = FirmaAyarlari()
        db.add(ayarlar)
        db.commit()
        db.refresh(ayarlar)
    return ayarlar


def sistem_ayarlarini_kaydet(
    db: Session,
    kullanici_adi: str,
    ip_adresi: str,
    islem_loglari_aktif: bool,
    otomatik_yedekleme_aktif: bool,
    bakim_modu_aktif: bool,
) -> FirmaAyarlari:
    ayarlar = sistem_ayarlari_getir(db)
    ayarlar.islem_loglari_aktif = islem_loglari_aktif
    ayarlar.otomatik_yedekleme_aktif = otomatik_yedekleme_aktif
    ayarlar.bakim_modu_aktif = bakim_modu_aktif
    islem_logla_veri(
        db, kullanici_adi, ip_adresi, "Ayarlar", "Sistem ayarları güncellendi",
        f"Log: {'açık' if islem_loglari_aktif else 'kapalı'}, otomatik yedek: {'açık' if otomatik_yedekleme_aktif else 'kapalı'}, bakım: {'açık' if bakim_modu_aktif else 'kapalı'}",
        zorla=True,
    )
    db.commit()
    return ayarlar


def bakim_modu_aktif_mi(db: Session) -> bool:
    ayarlar = firma_getir(db)
    return bool(ayarlar and ayarlar.bakim_modu_aktif)


def _json_degerine_cevir(deger):
    if isinstance(deger, datetime):
        return {"__tip__": "datetime", "deger": deger.isoformat()}
    if isinstance(deger, bytes):
        return {"__tip__": "bytes", "deger": deger.hex()}
    return deger


def sistem_yedegi_olustur(db: Session) -> tuple[bytes, str, int]:
    """Veritabanından taşınabilir, okunabilir ZIP/JSON yedeği üretir."""
    metadata = MetaData()
    metadata.reflect(bind=db.bind)
    veri = {"surum": 1, "olusturma_zamani": datetime.utcnow().isoformat(), "tablolar": {}}
    toplam_satir = 0
    for tablo in metadata.sorted_tables:
        satirlar = []
        for satir in db.execute(select(tablo)).mappings():
            satirlar.append({anahtar: _json_degerine_cevir(deger) for anahtar, deger in satir.items()})
        veri["tablolar"][tablo.name] = satirlar
        toplam_satir += len(satirlar)
    tampon = BytesIO()
    with ZipFile(tampon, "w", ZIP_DEFLATED) as dosya:
        dosya.writestr("muys-yedek.json", json.dumps(veri, ensure_ascii=False, indent=2))
    dosya_adi = f"muys-yedek-{datetime.now():%Y%m%d-%H%M%S}.zip"
    return tampon.getvalue(), dosya_adi, toplam_satir


def firma_adi_getir(db: Session) -> str:
    firma = firma_getir(db)
    return firma.firma_adi if firma and firma.firma_adi else "MÜYS"


def firma_ozeti_getir(db: Session) -> tuple[str, str]:
    firma = firma_getir(db)
    if not firma:
        return "MÜYS", ""
    if firma.logo_verisi:
        zaman = int(firma.updated_at.timestamp()) if firma.updated_at else 0
        return firma.firma_adi or "MÜYS", f"/firma-logo?v={zaman}"
    return firma.firma_adi or "MÜYS", firma.logo_yolu or ""


def _logo_dosyasini_dogrula(logo_dosyasi: tuple[str, bytes]) -> str:
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
    return {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }[gercek_uzanti]


def firma_bilgilerini_kaydet(db: Session, kullanici_adi: str, ip_adresi: str, logo_dosyasi: tuple[str, bytes] | None = None, **alanlar):
    firma = firma_getir(db)
    if not firma:
        firma = FirmaAyarlari()
        db.add(firma)
    for alan, deger in alanlar.items():
        setattr(firma, alan, deger)
    if logo_dosyasi:
        firma.logo_mime_turu = _logo_dosyasini_dogrula(logo_dosyasi)
        firma.logo_verisi = logo_dosyasi[1]
        firma.logo_yolu = ""
    islem_logla_veri(db, kullanici_adi, ip_adresi, "Ayarlar", "Firma bilgileri güncellendi", alanlar.get("firma_adi", ""))
    db.commit()
    return firma


def excel_sablon_verileri(db: Session):
    istasyon_kodlari = {istasyon.id: istasyon.kodu for istasyon in db.query(Istasyon).all()}
    personel_istasyon_kodlari = {}
    for atama in db.query(PersonelIstasyon).filter(PersonelIstasyon.aktif.is_(True)).all():
        kod = istasyon_kodlari.get(atama.istasyon_id)
        if kod:
            personel_istasyon_kodlari.setdefault(atama.personel_id, []).append(kod)
    urun_istasyon_kodlari = {}
    for atama in db.query(UrunIstasyon).filter(UrunIstasyon.aktif.is_(True)).all():
        kod = istasyon_kodlari.get(atama.istasyon_id)
        if kod:
            urun_istasyon_kodlari.setdefault(atama.urun_id, []).append(kod)
    return {
        "firma": firma_getir(db),
        "musteriler": db.query(Musteri).order_by(Musteri.id).all(),
        "urunler": db.query(Urun).order_by(Urun.kodu).all(),
        "personeller": db.query(Personel).order_by(Personel.kodu).all(),
        "istasyonlar": db.query(Istasyon).order_by(Istasyon.kodu).all(),
        "makineler": db.query(Makine).order_by(Makine.kodu).all(),
        "siniflar": db.query(UrunSinifi).order_by(UrunSinifi.kodu).all(),
        "stok_turleri": db.query(StokUrunTuru).filter(StokUrunTuru.aktif.is_(True), StokUrunTuru.uretilen.is_(False)).order_by(StokUrunTuru.adi).all(),
        "stok_siniflari": db.query(StokUrunSinifi).filter(StokUrunSinifi.aktif.is_(True)).order_by(StokUrunSinifi.adi).all(),
        "personel_istasyon_kodlari": personel_istasyon_kodlari,
        "urun_istasyon_kodlari": urun_istasyon_kodlari,
    }


def excel_indirme_logu(db: Session, kullanici_adi: str, ip_adresi: str, detay: str):
    islem_logla_veri(db, kullanici_adi, ip_adresi, "Excel", "Excel şablonu indirildi", detay, commit=True)
