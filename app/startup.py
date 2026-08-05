from app import models  # noqa: F401 - tüm tabloları SQLAlchemy metadata'ya kaydeder
from app.database import Base, SessionLocal, engine
from app.migrations import uyumluluk_migrationlarini_uygula
from app.setup import setup_database


def uygulamayi_hazirla() -> None:
    Base.metadata.create_all(bind=engine)
    uyumluluk_migrationlarini_uygula(engine)
    db = SessionLocal()
    try:
        setup_database(db)
    finally:
        db.close()
