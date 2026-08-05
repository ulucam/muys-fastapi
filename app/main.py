from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy import inspect, text

from app.database import Base, engine, SessionLocal
from app.setup import setup_database
# Bu modeller doğrudan içe aktarılır; eski veritabanlarında tabloların da
# uygulama başlarken oluşturulmasını garanti eder.
from app.models.firma_ayarlari import FirmaAyarlari
from app.models.islem_logu import IslemLogu
from app.models.excel_aktarim_taslagi import ExcelAktarimTaslagi
from app.models.personel import Personel
from app.models.istasyon import Istasyon
from app.models.makine import Makine
from app.models.personel_makine import PersonelMakine
from app.models.puantaj import Puantaj
from app.models.urun_sinifi import UrunSinifi
from app.models.urun_sinif_operasyon import UrunSinifOperasyon

from app.routes import auth
from app.routes import dashboard
from app.routes import kullanicilar
from app.routes import musteriler
from app.routes import ayarlar
from app.routes import profil
from app.routes import siparis_sayfasi
from app.routes import uretim_tanimlari
from app.routes import stok_sayfalari


# Veritabanı tablolarını oluştur
Base.metadata.create_all(bind=engine)

# Eski kurulumlara müşteri türü alanını ekle.
with engine.begin() as connection:
    sutunlar = {sutun["name"] for sutun in inspect(connection).get_columns("musteriler")}
    if "musteri_turu" not in sutunlar:
        connection.execute(
            text("ALTER TABLE musteriler ADD COLUMN musteri_turu VARCHAR(30) NOT NULL DEFAULT 'Alıcı'")
        )
    urun_sutunlari = {sutun["name"] for sutun in inspect(connection).get_columns("urunler")}
    if "urun_sinifi_id" not in urun_sutunlari:
        connection.execute(text("ALTER TABLE urunler ADD COLUMN urun_sinifi_id INTEGER"))
    kullanici_sutunlari = {sutun["name"] for sutun in inspect(connection).get_columns("kullanicilar")}
    if "istasyon_id" not in kullanici_sutunlari:
        connection.execute(text("ALTER TABLE kullanicilar ADD COLUMN istasyon_id INTEGER REFERENCES istasyonlar(id)"))


# İlk kurulum
db = SessionLocal()
setup_database(db)
db.close()


app = FastAPI(
    title="MÜYS - Üretim Yönetim Sistemi"
)


app.mount(
    "/static",
    StaticFiles(directory="app/static"),
    name="static"
)


app.add_middleware(
    SessionMiddleware,
    secret_key="muys-secret-key-2026"
)


@app.middleware("http")
async def firma_bilgisi_ekle(request, call_next):
    db = SessionLocal()
    try:
        firma = db.query(FirmaAyarlari).first()
        request.state.firma_adi = firma.firma_adi if firma and firma.firma_adi else "MÜYS"
    finally:
        db.close()
    return await call_next(request)


# ROUTES
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(kullanicilar.router)
app.include_router(musteriler.router)
app.include_router(ayarlar.router)
app.include_router(profil.router)
app.include_router(siparis_sayfasi.router)
app.include_router(uretim_tanimlari.router)
app.include_router(stok_sayfalari.router)
