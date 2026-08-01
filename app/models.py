from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime

class Rol(Base):
    __tablename__ = "roller"
    id = Column(Integer, primary_key=True, index=True)
    adi = Column(String(50), unique=True, nullable=False)
    aciklama = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    kullanicilar = relationship("User", back_populates="rol")

class User(Base):
    __tablename__ = "kullanicilar"
    id = Column(Integer, primary_key=True, index=True)
    kullanici_adi = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    sifre_hash = Column(String(200), nullable=False)
    adi = Column(String(100))
    soyadi = Column(String(100))
    telefon = Column(String(20))
    rol_id = Column(Integer, ForeignKey("roller.id"), default=3)
    aktif = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    rol = relationship("Rol", back_populates="kullanicilar")
    siparisler = relationship("Siparis", back_populates="musteri")

class Musteri(Base):
    __tablename__ = "musteriler"
    id = Column(Integer, primary_key=True, index=True)
    kodu = Column(String(20), unique=True, index=True)
    adi = Column(String(100), nullable=False)
    telefon = Column(String(20))
    email = Column(String(100))
    adres = Column(Text)
    vergi_no = Column(String(20))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    siparisler = relationship("Siparis", back_populates="musteri")

class Urun(Base):
    __tablename__ = "urunler"
    id = Column(Integer, primary_key=True, index=True)
    kodu = Column(String(20), unique=True, index=True, nullable=False)
    adi = Column(String(100), nullable=False)
    aciklama = Column(Text)
    birim = Column(String(10), default="Adet")
    urun_tipi = Column(String(20), default="Mamul")  # Hammadde, YariMamul, Mamul, TicariMamul
    tahmini_uretim_suresi = Column(Float, default=0)
    min_stok = Column(Float, default=0)
    mevcut_stok = Column(Float, default=0)
    birim_fiyat = Column(Float, default=0)
    malzeme = Column(String(50))
    kalinlik = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    siparis_kalemleri = relationship("SiparisKalem", back_populates="urun")

class Siparis(Base):
    __tablename__ = "siparisler"
    id = Column(Integer, primary_key=True, index=True)
    siparis_no = Column(String(30), unique=True, nullable=False)
    musteri_id = Column(Integer, ForeignKey("musteriler.id"))
    siparis_tarihi = Column(DateTime, default=datetime.utcnow)
    teslim_tarihi = Column(DateTime)
    durum = Column(String(20), default="Beklemede")  # Beklemede, Uretimde, Tamamlandi
    notlar = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    musteri = relationship("Musteri", back_populates="siparisler")
    kalemler = relationship("SiparisKalem", back_populates="siparis", cascade="all, delete-orphan")

class SiparisKalem(Base):
    __tablename__ = "siparis_kalemleri"
    id = Column(Integer, primary_key=True, index=True)
    siparis_id = Column(Integer, ForeignKey("siparisler.id"))
    urun_id = Column(Integer, ForeignKey("urunler.id"))
    miktar = Column(Float, nullable=False)
    uretilen_miktar = Column(Float, default=0)
    durum = Column(String(20), default="Beklemede")
    
    siparis = relationship("Siparis", back_populates="kalemler")
    urun = relationship("Urun", back_populates="siparis_kalemleri")
