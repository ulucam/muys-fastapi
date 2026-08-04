from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String

from app.database import Base


class Personel(Base):
    __tablename__ = "personeller"

    id = Column(Integer, primary_key=True)
    kodu = Column(String(50), unique=True, nullable=False, index=True)
    ad_soyad = Column(String(150), nullable=False)
    departman = Column(String(100), default="")
    gorev = Column(String(100), default="")
    aktif = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
