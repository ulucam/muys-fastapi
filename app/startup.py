from app import models  # noqa: F401 - tüm tabloları SQLAlchemy metadata'ya kaydeder
from app.database import Base, SessionLocal, engine
from app.migrations import uyumluluk_migrationlarini_uygula
from app.setup import setup_database
from app.services.uretim_tanimlari_service import urun_turlerini_standartlastir
from app.services.stok_service import stok_turlerini_standartlastir


def uygulamayi_hazirla() -> None:
    Base.metadata.create_all(bind=engine)
    uyumluluk_migrationlarini_uygula(engine)
    db = SessionLocal()
    try:
        setup_database(db)
        stok_turlerini_standartlastir(db)
        urun_turlerini_standartlastir(db)
    finally:
        db.close()
