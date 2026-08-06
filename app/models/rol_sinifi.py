from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text

from app.database import Base


class RolSinifi(Base):
    __tablename__ = "rol_siniflari"

    id = Column(Integer, primary_key=True)
    adi = Column(String(30), unique=True, nullable=False, index=True)
    seviye = Column(Integer, nullable=False, default=10)
    kullanici_ekleyebilir = Column(Boolean, nullable=False, default=False)
    yetkiler = Column(Text, nullable=False, default="")
    aciklama = Column(String(250), nullable=False, default="")
    sistem_rolu = Column(Boolean, nullable=False, default=False)
    aktif = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
