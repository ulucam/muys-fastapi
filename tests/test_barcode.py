"""app.utils.barcode birim testleri (EAN-13)."""

import pytest

from app.utils.barcode import barkod_uret, ean13_dogrula, ean13_kontrol_rakami


class TestEan13KontrolRakami:
    def test_bilinen_deger(self):
        # 869051201234 -> kontrol rakamı 3
        assert ean13_kontrol_rakami("869051201234") == 3

    def test_diger_bilinen(self):
        # 400638133393 -> kontrol rakamı 1
        assert ean13_kontrol_rakami("400638133393") == 1

    def test_hizli_gecerli(self):
        assert ean13_kontrol_rakami("000000000000") == 0

    def test_uzunluk_hatasi(self):
        with pytest.raises(ValueError):
            ean13_kontrol_rakami("123")

    def test_harf_hatasi(self):
        with pytest.raises(ValueError):
            ean13_kontrol_rakami("86905120123A")


class TestEan13Dogrula:
    def test_gecerli(self):
        assert ean13_dogrula("8690512012343") is True

    def test_gecersiz_rakam(self):
        assert ean13_dogrula("8690512012344") is False

    def test_kisa(self):
        assert ean13_dogrula("86905120123") is False

    def test_harf(self):
        assert ean13_dogrula("86905120123A3") is False


class TestBarkodUret:
    def test_tam_barkod(self):
        assert barkod_uret("869051201234") == "8690512012343"

    def test_uretilen_dogrulanir(self):
        for on_ek in ("869051201234", "400638133393", "123456789012"):
            assert ean13_dogrula(barkod_uret(on_ek))
