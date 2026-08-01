
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from datetime import datetime

from app.database import Base


class Musteri(Base):

    __tablename__ = "musteriler"


    id = Column(
        Integer,
        primary_key=True,
        index=True
    )


    # Firma / müşteri kodu
    kodu = Column(
        String(30),
        unique=True,
        index=True
    )


    # Firma veya kişi adı
    adi = Column(
        String(150),
        nullable=False
    )


    # Yetkili kişi
    yetkili = Column(
        String(100)
    )


    telefon = Column(
        String(30)
    )


    email = Column(
        String(100)
    )


    adres = Column(
        Text
    )


    vergi_no = Column(
        String(50)
    )


    notlar = Column(
        Text
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