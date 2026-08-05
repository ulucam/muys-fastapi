from datetime import date, datetime

from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String, UniqueConstraint

from app.database import Base


class Puantaj(Base):
    __tablename__ = "puantajlar"
    __table_args__ = (UniqueConstraint("personel_id", "tarih", name="uq_puantaj_personel_tarih"),)

    id = Column(Integer, primary_key=True)
    personel_id = Column(Integer, ForeignKey("personeller.id"), nullable=False, index=True)
    tarih = Column(Date, default=date.today, nullable=False, index=True)
    durum = Column(String(30), default="Geldi", nullable=False)
    aciklama = Column(String(250), default="")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
