from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey
from datetime import datetime

from app.database import Base


class StokHareket(Base):

    __tablename__ = "stok_hareketleri"


    id = Column(
        Integer,
        primary_key=True,
        index=True
    )


    # Hangi ürün
    urun_id = Column(
        Integer,
        ForeignKey("urunler.id"),
        nullable=False
    )


    # Giriş / Çıkış
    hareket_tipi = Column(
        String(20),
        nullable=False
    )


    # Miktar
    miktar = Column(
        Float,
        nullable=False
    )


    # Sebep
    # Satın Alma, Üretim, Sevkiyat vb.
    aciklama = Column(
        String(250)
    )


    # Referans
    # Sipariş no, üretim no vb.
    referans = Column(
        String(50)
    )


    tarih = Column(
        DateTime,
        default=datetime.utcnow
    )