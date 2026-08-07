"""app.dependencies / app.security birim testleri."""

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models  # noqa: F401
from app.database import Base
from app.dependencies import kullanici_yonetim_kontrol, yetki_kontrol
from app.models.rol_sinifi import RolSinifi


class FakeRequest:
    def __init__(self, session):
        self.session = session


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
    oturum.add(RolSinifi(adi="Depo", seviye=40, kullanici_ekleyebilir=False, yetkiler="", sistem_rolu=False, aktif=True))
    oturum.add(RolSinifi(adi="Y\u00f6netici", seviye=80, kullanici_ekleyebilir=True, yetkiler="", sistem_rolu=False, aktif=True))
    oturum.commit()
    yield oturum
    oturum.close()
    engine.dispose()


class TestYetkiKontrol:
    def test_izinli_rol(self):
        kontrol = yetki_kontrol(["Admin", "Y\u00f6netici"])
        assert kontrol(FakeRequest({"rol": "Admin"})) is True

    def test_izinsiz_rol(self):
        kontrol = yetki_kontrol(["Admin"])
        with pytest.raises(HTTPException) as exc:
            kontrol(FakeRequest({"rol": "Sat\u0131\u015f"}))
        assert exc.value.status_code == 403

    def test_rol_yok(self):
        kontrol = yetki_kontrol(["Admin"])
        with pytest.raises(HTTPException):
            kontrol(FakeRequest({}))


class TestKullaniciYonetimKontrol:
    def test_admin_gecer(self, db):
        # Admin rolü için DB'de karşılık olmasa bile izin verilir (hata fırlatılmaz)
        kullanici_yonetim_kontrol(FakeRequest({"rol": "Admin"}), db=db)

    def test_izni_olan_rol_gecer(self, db):
        rol = kullanici_yonetim_kontrol(FakeRequest({"rol": "Y\u00f6netici"}), db=db)
        assert rol is not None
        assert rol.kullanici_ekleyebilir is True

    def test_izni_olmayan_rol_red(self, db):
        with pytest.raises(HTTPException) as exc:
            kullanici_yonetim_kontrol(FakeRequest({"rol": "Depo"}), db=db)
        assert exc.value.status_code == 403

    def test_tanimsiz_rol_red(self, db):
        with pytest.raises(HTTPException) as exc:
            kullanici_yonetim_kontrol(FakeRequest({"rol": "Hayalet"}), db=db)
        assert exc.value.status_code == 403
