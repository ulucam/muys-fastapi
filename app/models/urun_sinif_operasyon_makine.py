from sqlalchemy import Column, ForeignKey, Integer, UniqueConstraint

from app.database import Base


class UrunSinifOperasyonMakine(Base):
    __tablename__ = "urun_sinif_operasyon_makineleri"
    __table_args__ = (UniqueConstraint("operasyon_id", "makine_id", name="uq_operasyon_makine"),)

    id = Column(Integer, primary_key=True)
    operasyon_id = Column(Integer, ForeignKey("urun_sinif_operasyonlari.id", ondelete="CASCADE"), nullable=False)
    makine_id = Column(Integer, ForeignKey("makineler.id"), nullable=False)
