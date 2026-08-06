
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from datetime import datetime

from app.database import Base


class Urun(Base):

    __tablename__ = "urunler"


    id = Column(
        Integer,
        primary_key=True,
        index=True
    )


    # Ürün kodu
    kodu = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True
    )


    # Ürün adı
    adi = Column(
        String(150),
        nullable=False
    )


    # Açıklama
    aciklama = Column(
        String(250)
    )


    # Hammadde / Yarı mamul / Mamul
    urun_tipi = Column(
        String(30),
        nullable=False,
        default="Mamul"
    )


    # Ölçü birimi
    # Adet, Kg, Metre vb.
    birim = Column(
        String(20),
        default="Adet"
    )


    # Mevcut stok
    mevcut_stok = Column(
        Float,
        default=0
    )


    # Minimum stok seviyesi
    min_stok = Column(
        Float,
        default=0
    )


    # Maksimum stok seviyesi
    max_stok = Column(
        Float,
        default=0
    )


    # Alış maliyeti
    maliyet = Column(
        Float,
        default=0
    )


    # Satış fiyatı
    satis_fiyati = Column(
        Float,
        default=0
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

    urun_sinifi_id = Column(
        Integer,
        ForeignKey("urun_siniflari.id"),
        nullable=True,
        index=True,
    )

    urun_cinsi = Column(
        String(100),
        default="",
        nullable=True,
    )

    marka = Column(String(100), default="", nullable=True)
    model = Column(String(100), default="", nullable=True)

    stok_urun_turu_id = Column(Integer, ForeignKey("stok_urun_turleri.id"), nullable=True, index=True)
    stok_urun_sinifi_id = Column(Integer, ForeignKey("stok_urun_siniflari.id"), nullable=True, index=True)
