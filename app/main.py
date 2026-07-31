from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.routes import auth, dashboard, musteriler, urunler, siparisler, uretim, stok, cari, excel
import os

# Veritabanı tablolarını oluştur
Base.metadata.create_all(bind=engine)

app = FastAPI(title="MÜYS API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static dosyalar
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Routes
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(musteriler.router)
app.include_router(urunler.router)
app.include_router(siparisler.router)
app.include_router(uretim.router)
app.include_router(stok.router)
app.include_router(cari.router)
app.include_router(excel.router)

# ===== HTML SAYFALARI =====

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/siparisler", response_class=HTMLResponse)
async def siparisler_page(request: Request):
    return templates.TemplateResponse("siparisler.html", {"request": request})

@app.get("/musteriler", response_class=HTMLResponse)
async def musteriler_page(request: Request):
    return templates.TemplateResponse("musteriler.html", {"request": request})

@app.get("/urunler", response_class=HTMLResponse)
async def urunler_page(request: Request):
    return templates.TemplateResponse("urunler.html", {"request": request})

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "message": "MÜYS API çalışıyor! 🚀"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000)
