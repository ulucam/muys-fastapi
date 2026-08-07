from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text

from app.database import Base


class Mesaj(Base):
    __tablename__ = "mesajlar"

    id = Column(Integer, primary_key=True)
    gonderen_id = Column(Integer, ForeignKey("kullanicilar.id"), nullable=False, index=True)
    alici_id = Column(Integer, ForeignKey("kullanicilar.id"), nullable=False, index=True)
    konusma_id = Column(Integer, ForeignKey("mesajlar.id"), nullable=True, index=True)
    konu_id = Column(Integer, ForeignKey("mesaj_konulari.id"), nullable=True, index=True)
    konu = Column(String(150), nullable=False)
    icerik = Column(Text, nullable=False)
    okundu = Column(Boolean, default=False, nullable=False, index=True)
    okunma_tarihi = Column(DateTime, nullable=True)
    gonderen_sildi = Column(Boolean, default=False, nullable=False)
    alici_sildi = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
