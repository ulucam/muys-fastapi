"""app.utils.helpers birim testleri."""

import pytest

from app.utils.helpers import kod_uret, metin, sayi, tarih_saat_str
from datetime import date, datetime


class TestMetin:
    def test_bos_deger(self):
        assert metin(None) == ""
        assert metin("") == ""

    def test_trim(self):
        assert metin("  abc  ") == "abc"

    def test_sayi_metne(self):
        assert metin(42) == "42"


class TestSayi:
    def test_tam_sayi(self):
        assert sayi("12", "Alan", tam_sayi=True) == 12

    def test_ondalik(self):
        assert sayi("12.5", "Alan") == 12.5

    def test_bos_ta_sifir(self):
        assert sayi(None, "Alan", bos_ta_sifir=True) == 0.0
        assert sayi("", "Alan", bos_ta_sifir=True) == 0.0

    def test_bos_ta_hata(self):
        with pytest.raises(ValueError):
            sayi(None, "Alan")

    def test_gecersiz_hata(self):
        with pytest.raises(ValueError, match="say\u0131sal"):
            sayi("abc", "Alan")

    def test_tam_sayi_ondalik_hata(self):
        with pytest.raises(ValueError):
            sayi("12.5", "Alan", tam_sayi=True)


class TestKodUret:
    def test_ilk_kod(self):
        assert kod_uret(set(), "M", 6) == "M000001"

    def test_siradaki_kod(self):
        # Orijinal davranış: mevcut en yüksek numaranın bir fazlası
        assert kod_uret({"M000001", "M000003"}, "M", 6) == "M000004"

    def test_dolu_olunca_otele(self):
        assert kod_uret({"M000001", "M000002"}, "M", 6) == "M000003"

    def test_personel_kodu(self):
        assert kod_uret({"P000001"}, "P", 6) == "P000002"


class TestTarihSaatStr:
    def test_datetime(self):
        assert tarih_saat_str(datetime(2026, 8, 7, 14, 30)) == "07.08.2026 14:30"

    def test_date(self):
        assert tarih_saat_str(date(2026, 8, 7)) == "07.08.2026"

    def test_none(self):
        assert tarih_saat_str(None) == ""
