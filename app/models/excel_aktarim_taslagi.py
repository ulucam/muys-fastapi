from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from app.database import Base


class ExcelAktarimTaslagi(Base):
    """Önizlemesi yapılmış Excel verisini onay adımına kadar saklar."""

    __tablename__ = "excel_aktarim_taslaklari"

    id = Column(Integer, primary_key=True)
    token = Column(String(64), unique=True, nullable=False, index=True)
    veri = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
