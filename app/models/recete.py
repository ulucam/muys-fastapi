from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from datetime import datetime

from app.database import Base


class Recete(Base):

    __tablename__ = "receteler"


    id = Column(
        Integer,
        primary_key=True,
        index=True
    )


    # Hangi ürünün reçetesi
    urun_id = Column(
        Integer,
        ForeignKey("urunler.id"),
        nullable=False
    )


    recete_no = Column(
        String(50),
        unique=True,
        nullable=False
    )


    aciklama = Column(
        String(250)
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