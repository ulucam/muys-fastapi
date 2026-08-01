from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from datetime import datetime

from app.database import Base


class Siparis(Base):

    __tablename__ = "siparisler"


    id = Column(
        Integer,
        primary_key=True,
        index=True
    )


    # Sipariş numarası
    siparis_no = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True
    )


    # Müşteri bağlantısı
    musteri_id = Column(
        Integer,
        ForeignKey("musteriler.id"),
        nullable=False
    )


    # Sipariş durumu
    durum = Column(
        String(30),
        default="Beklemede"
    )


    # Sipariş tarihi
    siparis_tarihi = Column(
        DateTime,
        default=datetime.utcnow
    )


    # Teslim tarihi
    teslim_tarihi = Column(
        DateTime
    )


    # Açıklama
    aciklama = Column(
        String(500)
    )


    aktif = Column(
        Boolean,
        default=True
    )


    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )


    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )