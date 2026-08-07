from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, UniqueConstraint

from app.database import Base


class MesajKonusu(Base):
    __tablename__ = "mesaj_konulari"

    id = Column(Integer, primary_key=True)
    adi = Column(String(80), unique=True, nullable=False)
    renk = Column(String(20), default="primary", nullable=False)
    aktif = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class MesajKonusuYetkili(Base):
    __tablename__ = "mesaj_konusu_yetkilileri"
    __table_args__ = (UniqueConstraint("konu_id", "kullanici_id", name="uq_mesaj_konusu_yetkili"),)

    id = Column(Integer, primary_key=True)
    konu_id = Column(Integer, ForeignKey("mesaj_konulari.id", ondelete="CASCADE"), nullable=False, index=True)
    kullanici_id = Column(Integer, ForeignKey("kullanicilar.id", ondelete="CASCADE"), nullable=False, index=True)


class MesajAlici(Base):
    """Grup/konu mesajlarında kullanıcı bazlı teslim ve okundu durumu."""

    __tablename__ = "mesaj_alicilari"
    __table_args__ = (UniqueConstraint("mesaj_id", "kullanici_id", name="uq_mesaj_alici"),)

    id = Column(Integer, primary_key=True)
    mesaj_id = Column(Integer, ForeignKey("mesajlar.id", ondelete="CASCADE"), nullable=False, index=True)
    kullanici_id = Column(Integer, ForeignKey("kullanicilar.id", ondelete="CASCADE"), nullable=False, index=True)
    okundu = Column(Boolean, default=False, nullable=False, index=True)
    okunma_tarihi = Column(DateTime, nullable=True)
