"""app.utils.zaman birim testleri."""

from datetime import datetime, timezone

from app.utils.zaman import turkiye_saati


class TestTurkiyeSaati:
    def test_none(self):
        assert turkiye_saati(None) is None

    def test_naive_utc_kabul(self):
        # Naive datetime UTC kabul edilir, +3 saat ile İstanbul'a çevrilir
        sonuc = turkiye_saati(datetime(2026, 8, 7, 12, 0, 0))
        assert sonuc.hour == 15
        assert sonuc.tzinfo is not None

    def test_aware_utc(self):
        sonuc = turkiye_saati(datetime(2026, 8, 7, 12, 0, 0, tzinfo=timezone.utc))
        assert sonuc.hour == 15

    def test_istanbul_degismez(self):
        from zoneinfo import ZoneInfo
        ist = datetime(2026, 8, 7, 15, 0, 0, tzinfo=ZoneInfo("Europe/Istanbul"))
        sonuc = turkiye_saati(ist)
        assert sonuc.hour == 15
