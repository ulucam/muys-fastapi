from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    kullanici_adi = Column(String(50), unique=True, nullable=False, index=True)

    sifre = Column(String(255), nullable=False)

    ad_soyad = Column(String(100), nullable=False)

    email = Column(String(100), unique=True)

    telefon = Column(String(20))

    rol = Column(String(30), nullable=False)

    aktif = Column(Boolean, default=True)

    son_giris = Column(DateTime)

    created_at = Column(DateTime, default=datetime.utcnow)

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
