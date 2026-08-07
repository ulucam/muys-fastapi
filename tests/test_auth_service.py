"""app.services.auth_service entegrasyon testleri (bellek içi SQLite)."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models  # noqa: F401
from app.database import Base
from app.models.user import User
from app.password import sifre_olustur
from app.services.auth_service import kullanici_dogrula, sifre_dogrula, sifre_hashle


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
    oturum.add(
        User(
            kullanici_adi="testci",
            sifre=sifre_olustur("gizli-123"),
            ad_soyad="Test Kullan\u0131c\u0131",
            rol="Depo",
            aktif=True,
        )
    )
    oturum.commit()
    yield oturum
    oturum.close()
    engine.dispose()


class TestKullaniciDogrula:
    def test_basarili(self, db):
        kullanici = kullanici_dogrula(db, "testci", "gizli-123")
        assert kullanici is not None
        assert kullanici.kullanici_adi == "testci"

    def test_yanlis_sifre(self, db):
        assert kullanici_dogrula(db, "testci", "yanlis") is None

    def test_olmayan_kullanici(self, db):
        assert kullanici_dogrula(db, "yok", "gizli-123") is None

    def test_bos_girdi(self, db):
        assert kullanici_dogrula(db, None, None) is None
        assert kullanici_dogrula(db, "", "") is None

    def test_buyuk_kucuk_duyarlilik(self, db):
        assert kullanici_dogrula(db, "TESTCI", "gizli-123") is None


class TestSifreYardimcilar:
    def test_hashle_ve_dogrula(self):
        hashli = sifre_hashle("parola")
        assert sifre_dogrula("parola", hashli) is True
        assert sifre_dogrula("baska", hashli) is False
