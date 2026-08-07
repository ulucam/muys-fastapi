"""app.setup veritabanı entegrasyon testleri (bellek içi SQLite)."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models  # noqa: F401 - tüm tabloları metadata'ya kaydeder
from app.database import Base
from app.models.rol_sinifi import RolSinifi
from app.models.stok_urun_turu import StokUrunTuru
from app.models.user import User
from app.setup import setup_database


@pytest.fixture()
def db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    oturum = Session()
    yield oturum
    oturum.close()
    engine.dispose()


class TestSetupDatabase:
    def test_admin_olusturulur(self, db):
        setup_database(db)
        admin = db.query(User).filter(User.kullanici_adi == "admin").first()
        assert admin is not None
        assert admin.rol == "Admin"
        assert admin.aktif is True

    def test_admin_sifresi_hashli(self, db):
        setup_database(db)
        admin = db.query(User).filter(User.kullanici_adi == "admin").first()
        assert admin.sifre != "admin123"
        assert admin.sifre.startswith("$")

    def test_varsayilan_roller(self, db):
        setup_database(db)
        roller = db.query(RolSinifi).all()
        adlar = {r.adi for r in roller}
        assert {"Admin", "Patron", "Y\u00f6netici", "\u00dcretim", "Sat\u0131\u015f", "Depo", "Operat\u00f6r"} <= adlar

    def test_varsayilan_stok_turleri(self, db):
        setup_database(db)
        turler = db.query(StokUrunTuru).all()
        adlar = {t.adi for t in turler}
        assert "Hammadde" in adlar
        assert "Sarf Malzeme" in adlar

    def test_ikinci_calistirmada_tekil(self, db):
        setup_database(db)
        setup_database(db)
        sayi = db.query(User).filter(User.kullanici_adi == "admin").count()
        assert sayi == 1
