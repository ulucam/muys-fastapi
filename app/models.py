from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey, Date
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    kullanici_adi = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    sifre_hash = Column(String(200), nullable=False)
    adi = Column(String(100))
    soyadi = Column(String(100))
    rol = Column(String(20), default="Operator")
    aktif = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Musteri(Base):
    __tablename__ = "musteriler"
    id = Column(Integer, primary_key=True, index=True)
    firma_kodu = Column(String(20), unique=True, nullable=False)
    firma_adi = Column(String(100), nullable=False)
    yetkili = Column(String(100))
    telefon = Column(String(20))
    email = Column(String(100))
    il = Column(String(50))
    ilce = Column(String(50))
    acik_adres = Column(Text)
    vergi_no = Column(String(20))
    musteri_tipi = Column(String(20), default="Alıcı")
    odeme_tipi = Column(String(20), default="Vadeli")
    bakiye = Column(Float, default=0)
    toplam_borc = Column(Float, default=0)
    toplam_alacak = Column(Float, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    siparisler = relationship("Siparis", back_populates="musteri")
    cari_hareketler = relationship("CariHareket", back_populates="musteri")

class Urun(Base):
    __tablename__ = "urunler"
    id = Column(Integer, primary_key=True, index=True)
    kodu = Column(String(20), unique=True, nullable=False)
    adi = Column(String(100), nullable=False)
    birim = Column(String(10), default="Adet")
    urun_tipi = Column(String(20), default="Mamul")
    mevcut_stok = Column(Float, default=0)
    min_stok = Column(Float, default=0)
    birim_fiyat = Column(Float, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

class Siparis(Base):
    __tablename__ = "siparisler"
    id = Column(Integer, primary_key=True, index=True)
    siparis_no = Column(String(30), unique=True, nullable=False)
    musteri_id = Column(Integer, ForeignKey("musteriler.id"))
    siparis_tarihi = Column(DateTime, default=datetime.utcnow)
    teslim_tarihi = Column(Date)
    durum = Column(String(20), default="Beklemede")
    notlar = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    musteri = relationship("Musteri", back_populates="siparisler")
    kalemler = relationship("SiparisKalem", back_populates="siparis", cascade="all, delete-orphan")

class SiparisKalem(Base):
    __tablename__ = "siparis_kalemleri"
    id = Column(Integer, primary_key=True, index=True)
    siparis_id = Column(Integer, ForeignKey("siparisler.id"))
    urun_id = Column(Integer, ForeignKey("urunler.id"))
    miktar = Column(Float, nullable=False)
    birim_fiyat = Column(Float, default=0)
    toplam_tutar = Column(Float, default=0)
    siparis = relationship("Siparis", back_populates="kalemler")
    urun = relationship("Urun")

class CariHareket(Base):
    __tablename__ = "cari_hareketler"
    id = Column(Integer, primary_key=True, index=True)
    musteri_id = Column(Integer, ForeignKey("musteriler.id"))
    hareket_tipi = Column(String(30), nullable=False)
    tutar = Column(Float, nullable=False)
    borc = Column(Float, default=0)
    alacak = Column(Float, default=0)
    aciklama = Column(Text)
    referans_no = Column(String(50))
    vade_tarihi = Column(Date)
    odeme_durumu = Column(String(20), default="Bekliyor")
    odeme_tarihi = Column(Date)
    created_at = Column(DateTime, default=datetime.utcnow)
    musteri = relationship("Musteri", back_populates="cari_hareketler")
