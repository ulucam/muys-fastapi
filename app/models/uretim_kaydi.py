from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String

from app.database import Base


class UretimKaydi(Base):
    """Operatörün bir üretim emri için oluşturduğu fiili çalışma kaydı."""

    __tablename__ = "uretim_kayitlari"

    id = Column(Integer, primary_key=True, index=True)
    uretim_emri_id = Column(Integer, ForeignKey("uretim_emirleri.id"), nullable=False, index=True)
    personel_id = Column(Integer, ForeignKey("personeller.id"), nullable=False, index=True)
    istasyon_id = Column(Integer, ForeignKey("istasyonlar.id"), nullable=False, index=True)
    durum = Column(String(20), nullable=False, default="Devam Ediyor", index=True)
    baslangic = Column(DateTime, nullable=False, default=datetime.now)
    bitis = Column(DateTime, nullable=True)
    uretilen_miktar = Column(Float, nullable=False, default=0)
    fire_miktari = Column(Float, nullable=False, default=0)
    aciklama = Column(String(500), default="")
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
