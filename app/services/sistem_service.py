import platform
import sys

import fastapi
import sqlalchemy

from app.database import engine
from app.version import guncel_surumu_al


def sistem_bilgileri() -> list[tuple[str, str]]:
    """Çalışan uygulamanın güncel teknik özetini hazırlar."""
    veritabani = engine.url.get_backend_name()
    veritabani_adi = "PostgreSQL" if veritabani == "postgresql" else "SQLite" if veritabani == "sqlite" else veritabani.title()
    return [
        ("Program", "MÜYS - Üretim Yönetim Sistemi"),
        ("Sürüm", guncel_surumu_al()),
        ("Framework", f"FastAPI {fastapi.__version__}"),
        ("Veritabanı", f"{veritabani_adi} · SQLAlchemy {sqlalchemy.__version__}"),
        ("Python", platform.python_version()),
        ("Sunucu", platform.system()),
    ]
