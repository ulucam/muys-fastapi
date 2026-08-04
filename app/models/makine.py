from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String

from app.database import Base


class Makine(Base):
    __tablename__ = "makineler"

    id = Column(Integer, primary_key=True)
    kodu = Column(String(50), unique=True, nullable=False, index=True)
    adi = Column(String(150), nullable=False)
    istasyon_id = Column(Integer, ForeignKey("istasyonlar.id"), nullable=False)
    model = Column(String(100), default="")
    kapasite = Column(String(100), default="")
    aktif = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
