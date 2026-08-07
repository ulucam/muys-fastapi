from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from app.database import Base


class VapidAyari(Base):
    """Ortam değişkeni yoksa Web Push anahtarlarını kalıcı tutar."""

    __tablename__ = "vapid_ayarlari"

    id = Column(Integer, primary_key=True)
    public_key = Column(String(200), nullable=False)
    private_key = Column(Text, nullable=False)
    subject = Column(String(250), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
