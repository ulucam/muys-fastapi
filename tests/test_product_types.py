"""app.product_types birim testleri."""

from app.product_types import URUN_TURLERI, urun_turunu_normalize_et


class TestUrunTuruNormalize:
    def test_kimlik(self):
        for tur in URUN_TURLERI:
            assert urun_turunu_normalize_et(tur) == tur

    def test_kucuk_harf(self):
        assert urun_turunu_normalize_et("hammadde") == "Hammadde"
        assert urun_turunu_normalize_et("mamul") == "Mam\u00fcl"

    def test_turkce_karakterler(self):
        assert urun_turunu_normalize_et("Mam\u00fcl") == "Mam\u00fcl"
        assert urun_turunu_normalize_et("Yar\u0131 Mam\u00fcl") == "Yar\u0131 Mam\u00fcl"
        assert urun_turunu_normalize_et("Sarf Malzeme") == "Sarf Malzeme"

    def test_bos_degerler(self):
        assert urun_turunu_normalize_et(None) == ""
        assert urun_turunu_normalize_et("") == ""

    def test_taninsiz(self):
        assert urun_turunu_normalize_et("Bilinmeyen") == ""
        assert urun_turunu_normalize_et(12345) == ""
