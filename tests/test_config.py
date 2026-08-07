"""app.config birim testleri."""

import importlib


class TestConfig:
    def test_varsayilanlar(self):
        import app.config
        cfg = app.config.Config
        assert cfg.ALGORITHM == "HS256"
        assert cfg.ACCESS_TOKEN_EXPIRE_MINUTES == 10080
        assert cfg.SECRET_KEY
        assert cfg.DATABASE_URL.startswith("sqlite")

    def test_env_override(self, monkeypatch):
        monkeypatch.setenv("SECRET_KEY", "test-anahtar")
        monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
        import app.config
        importlib.reload(app.config)
        try:
            assert app.config.Config.SECRET_KEY == "test-anahtar"
            assert app.config.Config.ACCESS_TOKEN_EXPIRE_MINUTES == 60
        finally:
            importlib.reload(app.config)
