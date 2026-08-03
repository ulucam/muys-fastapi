from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

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
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
