"""app.password birim testleri (pwdlib/argon2)."""

from app.password import sifre_kontrol, sifre_olustur


class TestSifre:
    def test_hash_uretir(self):
        hashli = sifre_olustur("gizli-sifre")
        assert hashli != "gizli-sifre"
        assert len(hashli) > 20

    def test_dogrulama(self):
        hashli = sifre_olustur("gizli-sifre")
        assert sifre_kontrol("gizli-sifre", hashli) is True

    def test_yanlis_sifre(self):
        hashli = sifre_olustur("gizli-sifre")
        assert sifre_kontrol("yanlis", hashli) is False

    def test_tuz_farkliligi(self):
        h1 = sifre_olustur("ayni-sifre")
        h2 = sifre_olustur("ayni-sifre")
        assert h1 != h2
