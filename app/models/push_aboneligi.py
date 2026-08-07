from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, UniqueConstraint

from app.database import Base


class PushAboneligi(Base):
    """Bir kullanıcının tarayıcı/cihaz bazlı Web Push aboneliği."""

    __tablename__ = "push_abonelikleri"
    __table_args__ = (UniqueConstraint("endpoint", name="uq_push_endpoint"),)

    id = Column(Integer, primary_key=True)
    kullanici_id = Column(Integer, ForeignKey("kullanicilar.id", ondelete="CASCADE"), nullable=False, index=True)
    endpoint = Column(String(1000), nullable=False)
    p256dh_key = Column(String(300), nullable=False)
    auth_key = Column(String(300), nullable=False)
    cihaz_adi = Column(String(200), default="", nullable=False)
    aktif = Column(Boolean, default=True, nullable=False, index=True)
    son_kullanim = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
