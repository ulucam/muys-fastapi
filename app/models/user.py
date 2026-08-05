from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from datetime import datetime

from app.database import Base


class User(Base):

    __tablename__ = "kullanicilar"


    id = Column(
        Integer,
        primary_key=True,
        index=True
    )


    kullanici_adi = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True
    )


    sifre = Column(
        String(255),
        nullable=False
    )


    ad_soyad = Column(
        String(100),
        nullable=False
    )


    email = Column(
        String(100),
        unique=True
    )


    telefon = Column(
        String(20)
    )


    rol = Column(
        String(30),
        nullable=False
    )


    aktif = Column(
        Boolean,
        default=True
    )


    son_giris = Column(
        DateTime
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

    # Operatörün görev yaptığı üretim istasyonu. Diğer rollerde boş tutulur.
    istasyon_id = Column(
        Integer,
        ForeignKey("istasyonlar.id"),
        nullable=True
    )

    personel_id = Column(
        Integer,
        ForeignKey("personeller.id"),
        nullable=True,
        index=True
    )
