from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Integer, String
from app.database import Base


class StokUrunSinifi(Base):
    __tablename__ = "stok_urun_siniflari"
    id = Column(Integer, primary_key=True)
    adi = Column(String(100), unique=True, nullable=False)
    aktif = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
