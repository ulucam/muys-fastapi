from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from datetime import datetime

from app.database import Base


class Musteri(Base):

    __tablename__ = "musteriler"


    id = Column(
        Integer,
        primary_key=True,
        index=True
    )


    # Müşteri kodu
    # Örnek: M000001
    musteri_kodu = Column(
        String(30),
        unique=True,
        nullable=False,
        index=True
    )


    # Firma bilgileri

    firma_adi = Column(
        String(150),
        nullable=False,
        index=True
    )


    yetkili = Column(
        String(100),
        nullable=True
    )


    telefon = Column(
        String(30),
        nullable=True
    )


    email = Column(
        String(120),
        nullable=True
    )



    # Vergi bilgileri

    vergi_dairesi = Column(
        String(100),
        nullable=True
    )


    vergi_no = Column(
        String(30),
        nullable=True,
        index=True
    )



    # Adres bilgileri

    il = Column(
        String(50),
        nullable=True
    )


    ilce = Column(
        String(50),
        nullable=True
    )


    adres = Column(
        Text,
        nullable=True
    )



    # Durum

    aktif = Column(
        Boolean,
        default=True,
        nullable=False
    )



    # Açıklama / notlar

    aciklama = Column(
        Text,
        nullable=True
    )



    # Sistem tarihleri

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )


    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )