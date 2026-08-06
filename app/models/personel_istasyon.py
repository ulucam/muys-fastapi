from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, UniqueConstraint

from app.database import Base


class PersonelIstasyon(Base):
    """Personelin çalışabileceği istasyonları tutar."""

    __tablename__ = "personel_istasyon_atamalari"
    __table_args__ = (UniqueConstraint("personel_id", "istasyon_id", name="uq_personel_istasyon"),)

    id = Column(Integer, primary_key=True)
    personel_id = Column(Integer, ForeignKey("personeller.id"), nullable=False, index=True)
    istasyon_id = Column(Integer, ForeignKey("istasyonlar.id"), nullable=False, index=True)
    aktif = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
