from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint

from app.database import Base


class UrunSinifOperasyon(Base):
    __tablename__ = "urun_sinif_operasyonlari"
    __table_args__ = (UniqueConstraint("urun_sinifi_id", "sira_no", name="uq_urun_sinifi_operasyon_sira"),)

    id = Column(Integer, primary_key=True)
    urun_sinifi_id = Column(Integer, ForeignKey("urun_siniflari.id"), nullable=False)
    sira_no = Column(Integer, nullable=False)
    istasyon_id = Column(Integer, ForeignKey("istasyonlar.id"), nullable=False)
    makine_id = Column(Integer, ForeignKey("makineler.id"), nullable=True)
    operasyon_adi = Column(String(150), nullable=False)
    hedef_cevrim_suresi = Column(Float, default=0)
    kontrol_noktasi = Column(String(250), default="")
    aktif = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
