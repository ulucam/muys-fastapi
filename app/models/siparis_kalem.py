from sqlalchemy import Column, Integer, Float, String, DateTime, Boolean, ForeignKey
from datetime import datetime

from app.database import Base


class SiparisKalem(Base):

    __tablename__ = "siparis_kalemleri"


    id = Column(
        Integer,
        primary_key=True,
        index=True
    )


    # Bağlı olduğu sipariş
    siparis_id = Column(
        Integer,
        ForeignKey("siparisler.id"),
        nullable=False
    )


    # Sipariş edilen ürün
    urun_id = Column(
        Integer,
        ForeignKey("urunler.id"),
        nullable=False
    )


    # Sıra numarası
    sira_no = Column(
        Integer,
        default=1
    )


    # Miktar
    miktar = Column(
        Float,
        nullable=False,
        default=1
    )


    # Birim
    birim = Column(
        String(20),
        default="Adet"
    )


    # Üretim durumu
    durum = Column(
        String(30),
        default="Beklemede"
    )


    # Üretilen miktar
    uretilen_miktar = Column(
        Float,
        default=0
    )


    # Sevk edilen miktar
    sevk_miktar = Column(
        Float,
        default=0
    )


    # Sipariş kalemine özel not
    notlar = Column(
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