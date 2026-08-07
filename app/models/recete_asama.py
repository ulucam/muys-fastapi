from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint

from app.database import Base


class ReceteAsama(Base):
    __tablename__ = "recete_asamalari"
    __table_args__ = (UniqueConstraint("recete_id", "sira_no", name="uq_recete_asama_sira"),)

    id = Column(Integer, primary_key=True)
    recete_id = Column(Integer, ForeignKey("receteler.id", ondelete="CASCADE"), nullable=False, index=True)
    sira_no = Column(Integer, nullable=False)
    istasyon_id = Column(Integer, ForeignKey("istasyonlar.id"), nullable=False, index=True)
    operasyon_adi = Column(String(150), nullable=False)
    hedef_cevrim_suresi = Column(Float, default=0, nullable=False)
    aciklama = Column(String(500), default="")
    aktif = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class ReceteAsamaMalzeme(Base):
    __tablename__ = "recete_asama_malzemeleri"
    __table_args__ = (UniqueConstraint("asama_id", "malzeme_id", name="uq_recete_asama_malzeme"),)

    id = Column(Integer, primary_key=True)
    asama_id = Column(Integer, ForeignKey("recete_asamalari.id", ondelete="CASCADE"), nullable=False, index=True)
    malzeme_id = Column(Integer, ForeignKey("urunler.id"), nullable=False, index=True)
    miktar = Column(Float, nullable=False, default=1)
    birim = Column(String(20), nullable=False, default="Adet")
    fire_orani = Column(Float, nullable=False, default=0)
    aciklama = Column(String(250), default="")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

