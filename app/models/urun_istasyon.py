from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, UniqueConstraint

from app.database import Base


class UrunIstasyon(Base):
    """Bir stok ürününün kullanılabildiği istasyonları tutar."""

    __tablename__ = "urun_istasyon_atamalari"
    __table_args__ = (UniqueConstraint("urun_id", "istasyon_id", name="uq_urun_istasyon"),)

    id = Column(Integer, primary_key=True)
    urun_id = Column(Integer, ForeignKey("urunler.id", ondelete="CASCADE"), nullable=False, index=True)
    istasyon_id = Column(Integer, ForeignKey("istasyonlar.id"), nullable=False, index=True)
    aktif = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
