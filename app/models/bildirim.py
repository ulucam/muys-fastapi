from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String

from app.database import Base


class Bildirim(Base):
    __tablename__ = "bildirimler"

    id = Column(Integer, primary_key=True)
    kullanici_id = Column(Integer, ForeignKey("kullanicilar.id", ondelete="CASCADE"), nullable=False, index=True)
    baslik = Column(String(120), nullable=False)
    mesaj = Column(String(500), nullable=False)
    tur = Column(String(30), default="bilgi", nullable=False)
    baglanti = Column(String(300), default="", nullable=False)
    okundu = Column(Boolean, default=False, nullable=False, index=True)
    okunma_tarihi = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
