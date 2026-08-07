from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint

from app.database import Base


class UretimPlani(Base):
    __tablename__ = "uretim_planlari"

    id = Column(Integer, primary_key=True)
    plan_no = Column(String(50), unique=True, nullable=False, index=True)
    hedef_turu = Column(String(20), nullable=False)  # Siparis / Stok
    siparis_kalem_id = Column(Integer, ForeignKey("siparis_kalemleri.id"), nullable=True, index=True)
    urun_id = Column(Integer, ForeignKey("urunler.id"), nullable=False, index=True)
    recete_id = Column(Integer, ForeignKey("receteler.id"), nullable=False, index=True)
    miktar = Column(Float, nullable=False)
    durum = Column(String(30), nullable=False, default="Planlandı", index=True)
    aciklama = Column(String(500), default="")
    aktif = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class UretimPlanAsamasi(Base):
    __tablename__ = "uretim_plan_asamalari"
    __table_args__ = (UniqueConstraint("uretim_plani_id", "sira_no", name="uq_plan_asama_sira"),)

    id = Column(Integer, primary_key=True)
    uretim_plani_id = Column(Integer, ForeignKey("uretim_planlari.id", ondelete="CASCADE"), nullable=False, index=True)
    recete_asama_id = Column(Integer, ForeignKey("recete_asamalari.id"), nullable=False)
    sira_no = Column(Integer, nullable=False)
    istasyon_id = Column(Integer, ForeignKey("istasyonlar.id"), nullable=False, index=True)
    operasyon_adi = Column(String(150), nullable=False)
    hedef_miktar = Column(Float, nullable=False)
    tamamlanan_miktar = Column(Float, nullable=False, default=0)
    fire_miktari = Column(Float, nullable=False, default=0)
    durum = Column(String(30), nullable=False, default="Bekliyor", index=True)
    baslama_tarihi = Column(DateTime, nullable=True)
    bitis_tarihi = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

