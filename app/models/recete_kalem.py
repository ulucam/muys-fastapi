from sqlalchemy import Column, Integer, Float, String, DateTime, Boolean, ForeignKey
from datetime import datetime

from app.database import Base


class ReceteKalem(Base):

    __tablename__ = "recete_kalemleri"


    id = Column(
        Integer,
        primary_key=True,
        index=True
    )


    # Hangi reçeteye ait
    recete_id = Column(
        Integer,
        ForeignKey("receteler.id"),
        nullable=False
    )


    # Kullanılan malzeme / yarı mamul
    malzeme_id = Column(
        Integer,
        ForeignKey("urunler.id"),
        nullable=False
    )


    # Kullanım miktarı
    miktar = Column(
        Float,
        nullable=False,
        default=1
    )


    # Adet, Kg, Metre vb.
    birim = Column(
        String(20),
        default="Adet"
    )


    # Üretimde hangi sırada kullanılacak
    sira_no = Column(
        Integer,
        default=1
    )


    # Fire yüzdesi
    fire_orani = Column(
        Float,
        default=0
    )


    # Aktif/Pasif
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