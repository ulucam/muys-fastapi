from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, LargeBinary, String, Text

from app.database import Base


class FirmaAyarlari(Base):
    __tablename__ = "firma_ayarlari"

    id = Column(Integer, primary_key=True)
    firma_adi = Column(String(150), default="")
    vergi_no = Column(String(30), default="")
    vergi_dairesi = Column(String(100), default="")
    telefon = Column(String(30), default="")
    email = Column(String(120), default="")
    web_sitesi = Column(String(200), default="")
    adres = Column(Text, default="")
    logo_yolu = Column(String(300), default="")
    logo_verisi = Column(LargeBinary, nullable=True)
    logo_mime_turu = Column(String(100), default="")
    islem_loglari_aktif = Column(Boolean, nullable=False, default=True)
    otomatik_yedekleme_aktif = Column(Boolean, nullable=False, default=False)
    bakim_modu_aktif = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
