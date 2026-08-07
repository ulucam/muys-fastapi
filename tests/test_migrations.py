"""app.migrations entegrasyon testleri (bellek içi SQLite)."""

import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.pool import StaticPool

from app.migrations import uyumluluk_migrationlarini_uygula


@pytest.fixture()
def eski_sema_engine():
    """Migration öncesi eski şemayı (eksik sütunlarla) kurar."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    with engine.begin() as baglanti:
        baglanti.execute(text("CREATE TABLE musteriler (id INTEGER PRIMARY KEY, adi VARCHAR(100))"))
        baglanti.execute(text("CREATE TABLE urunler (id INTEGER PRIMARY KEY, kodu VARCHAR(50))"))
        baglanti.execute(text("CREATE TABLE firma_ayarlari (id INTEGER PRIMARY KEY)"))
    yield engine
    engine.dispose()


class TestUyumlulukMigrationlari:
    def test_eksik_sutun_eklenir(self, eski_sema_engine):
        uyumluluk_migrationlarini_uygula(eski_sema_engine)
        sutunlar = {s["name"] for s in inspect(eski_sema_engine).get_columns("musteriler")}
        assert "musteri_turu" in sutunlar

    def test_urun_sutunlari(self, eski_sema_engine):
        uyumluluk_migrationlarini_uygula(eski_sema_engine)
        sutunlar = {s["name"] for s in inspect(eski_sema_engine).get_columns("urunler")}
        assert {"urun_sinifi_id", "marka", "model", "olcu"} <= sutunlar

    def test_firma_logo_sutunlari(self, eski_sema_engine):
        uyumluluk_migrationlarini_uygula(eski_sema_engine)
        sutunlar = {s["name"] for s in inspect(eski_sema_engine).get_columns("firma_ayarlari")}
        assert "logo_verisi" in sutunlar
        assert "logo_mime_turu" in sutunlar

    def test_ikinci_calisma_hatasiz(self, eski_sema_engine):
        uyumluluk_migrationlarini_uygula(eski_sema_engine)
        uyumluluk_migrationlarini_uygula(eski_sema_engine)  # idempotent olmalı
