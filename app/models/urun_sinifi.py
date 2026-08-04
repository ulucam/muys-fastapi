from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String

from app.database import Base


class UrunSinifi(Base):
    __tablename__ = "urun_siniflari"

    id = Column(Integer, primary_key=True)
    kodu = Column(String(50), unique=True, nullable=False, index=True)
    adi = Column(String(150), nullable=False)
    aciklama = Column(String(250), default="")
    aktif = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
