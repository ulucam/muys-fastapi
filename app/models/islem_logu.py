from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from app.database import Base


class IslemLogu(Base):
    __tablename__ = "islem_loglari"

    id = Column(Integer, primary_key=True)
    kullanici_adi = Column(String(50), nullable=False)
    modul = Column(String(50), nullable=False)
    islem = Column(String(100), nullable=False)
    detay = Column(Text, default="")
    ip_adresi = Column(String(45), default="")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
