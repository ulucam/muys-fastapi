from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.config import Config
from app.database import SessionLocal
from app.routes import (
    auth,
    ayarlar,
    dashboard,
    kullanicilar,
    musteriler,
    profil,
    siparis_sayfasi,
    stok_sayfalari,
    uretim_tanimlari,
)
from app.services.ayarlar_service import firma_ozeti_getir
from app.startup import uygulamayi_hazirla


@asynccontextmanager
async def lifespan(app: FastAPI):
    uygulamayi_hazirla()
    yield


app = FastAPI(
    title="MÜYS - Üretim Yönetim Sistemi",
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.add_middleware(SessionMiddleware, secret_key=Config.SECRET_KEY)


@app.middleware("http")
async def firma_bilgisi_ekle(request, call_next):
    db = SessionLocal()
    try:
        request.state.firma_adi, request.state.firma_logo_yolu = firma_ozeti_getir(db)
    finally:
        db.close()
    return await call_next(request)


app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(kullanicilar.router)
app.include_router(musteriler.router)
app.include_router(ayarlar.router)
app.include_router(profil.router)
app.include_router(siparis_sayfasi.router)
app.include_router(uretim_tanimlari.router)
app.include_router(stok_sayfalari.router)
