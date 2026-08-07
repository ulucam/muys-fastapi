"""app.version birim testleri."""

from app.version import YEREL_SURUM, guncel_surumu_al


class TestVersion:
    def test_yerel_surum_etiketi(self):
        assert YEREL_SURUM.startswith("v")

    def test_ag_yoksa_yerel_surum(self, monkeypatch):
        def patlayan(*args, **kwargs):
            raise OSError("ag kapali")

        import app.version
        monkeypatch.setattr(app.version, "urlopen", patlayan)
        guncel_surumu_al.cache_clear()
        assert guncel_surumu_al() == YEREL_SURUM
