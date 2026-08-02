from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.database import Base, engine

from app.database import SessionLocal
from app.setup import setup_database
from app.routes import auth
from app.routes import dashboard
from app.routes import kullanicilar
from app.routes import musteriler




Base.metadata.create_all(bind=engine)

from app.seed import admin_olustur
from app.database import SessionLocal

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


# ROUTES
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(kullanicilar.router)
app.include_router(musteriler.router)