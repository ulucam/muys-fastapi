from sqlalchemy import Column, Integer, Float, String, DateTime, Boolean, ForeignKey
from datetime import datetime

from app.database import Base


class UretimEmri(Base):

    __tablename__ = "uretim_emirleri"


    id = Column(
        Integer,
        primary_key=True,
        index=True
    )


    # Üretim emri numarası
    emir_no = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True
    )


    # Hangi sipariş kaleminden çıktı
    siparis_kalem_id = Column(
        Integer,
        ForeignKey("siparis_kalemleri.id")
    )


    # Üretilecek ürün
    urun_id = Column(
        Integer,
        ForeignKey("urunler.id"),
        nullable=False
    )


    # Üretim miktarı
    miktar = Column(
        Float,
        nullable=False
    )


    # Planlandı / Üretimde / Tamamlandı
    durum = Column(
        String(30),
        default="Planlandı"
    )


    baslama_tarihi = Column(
        DateTime
    )


    bitis_tarihi = Column(
        DateTime
    )


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