"""Uygulama genelinde paylaşılan Jinja2 şablon motoru.

``directory`` yolu ``__file__`` üzerinden çözümlenir; böylece uygulama
hangi çalışma dizininden başlatılırsa başlatılsın şablonlar bulunur.
"""

from pathlib import Path

from fastapi.templating import Jinja2Templates

# app/ klasörünün mutlak yolu (çalışma dizininden bağımsız)
APP_KLASORU = Path(__file__).resolve().parent
TEMPLATE_KLASORU = APP_KLASORU / "templates"
STATIK_KLASORU = APP_KLASORU / "static"

templates = Jinja2Templates(directory=str(TEMPLATE_KLASORU))
