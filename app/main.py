from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.config import Config
from app.database import SessionLocal
from app.models.rol_sinifi import RolSinifi
from app.routes import (
    auth,
    ayarlar,
    dashboard,
    iletisim,
    kullanicilar,
    musteriler,
    profil,
    push,
    siparis_sayfasi,
    stok_sayfalari,
    uretim_tanimlari,
)
from app.services.ayarlar_service import firma_ozeti_getir
from app.services.ayarlar_service import bakim_modu_aktif_mi
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
        rol_adi = request.session.get("rol", "")
        rol = db.query(RolSinifi).filter(RolSinifi.adi == rol_adi, RolSinifi.aktif.is_(True)).first()
        request.state.kullanici_ekleyebilir = bool(rol_adi == "Admin" or (rol and rol.kullanici_ekleyebilir))
        request.state.yedekleme_yapabilir = bool(rol_adi == "Admin" or (rol and rol.yedekleme_yapabilir))
        request.state.loglarini_gorebilir = bool(rol_adi == "Admin" or (rol and rol.loglarini_gorebilir))
        if (
            request.session.get("user_id")
            and rol_adi != "Admin"
            and bakim_modu_aktif_mi(db)
            and not request.url.path.startswith("/static/")
        ):
            request.session.clear()
            return RedirectResponse("/login?bakim=1", status_code=303)
    finally:
        db.close()
    return await call_next(request)


app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(iletisim.router)
app.include_router(push.router)
app.include_router(kullanicilar.router)
app.include_router(musteriler.router)
app.include_router(ayarlar.router)
app.include_router(profil.router)
app.include_router(siparis_sayfasi.router)
app.include_router(uretim_tanimlari.router)
app.include_router(stok_sayfalari.router)
