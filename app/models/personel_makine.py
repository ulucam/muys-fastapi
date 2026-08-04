from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint

from app.database import Base


class PersonelMakine(Base):
    __tablename__ = "personel_makine_atamalari"
    __table_args__ = (UniqueConstraint("personel_id", "makine_id", name="uq_personel_makine"),)

    id = Column(Integer, primary_key=True)
    personel_id = Column(Integer, ForeignKey("personeller.id"), nullable=False)
    makine_id = Column(Integer, ForeignKey("makineler.id"), nullable=False)
    rol = Column(String(100), default="Operatör")
    hedef_performans = Column(Float, default=100)
    aktif = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
