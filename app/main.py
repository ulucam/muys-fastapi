from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

from app.database import Base, engine

from app.routes import auth
from app.routes import dashboard
from app.routes import musteriler
from app.routes import urunler


Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="MÜYS"
)


app.add_middleware(
    SessionMiddleware,
    secret_key="gizli"
)


app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(musteriler.router)
app.include_router(urunler.router)