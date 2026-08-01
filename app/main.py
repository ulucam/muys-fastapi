from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
import os

# ===== KONFIG =====
DATABASE_URL = "sqlite:///./muys.db"
SECRET_KEY = "gizli-anahtar-2026"

# ===== VERİTABANI =====
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ===== MODELLER =====
class User(Base):
    __tablename__ = "kullanicilar"
    id = Column(Integer, primary_key=True, index=True)
    kullanici_adi = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    sifre = Column(String(200), nullable=False)  # Düz metin (basitlik için)
    adi = Column(String(100))
    aktif = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)

class Musteri(Base):
    __tablename__ = "musteriler"
    id = Column(Integer, primary_key=True, index=True)
    kodu = Column(String(20), unique=True)
    adi = Column(String(100), nullable=False)
    telefon = Column(String(20))
    email = Column(String(100))
    adres = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class Urun(Base):
    __tablename__ = "urunler"
    id = Column(Integer, primary_key=True, index=True)
    kodu = Column(String(20), unique=True, nullable=False)
    adi = Column(String(100), nullable=False)
    birim = Column(String(10), default="Adet")
    urun_tipi = Column(String(20), default="Mamul")
    mevcut_stok = Column(Float, default=0)
    min_stok = Column(Float, default=0)
    birim_fiyat = Column(Float, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

class Siparis(Base):
    __tablename__ = "siparisler"
    id = Column(Integer, primary_key=True, index=True)
    siparis_no = Column(String(30), unique=True)
    musteri_id = Column(Integer, ForeignKey("musteriler.id"))
    durum = Column(String(20), default="Beklemede")
    created_at = Column(DateTime, default=datetime.utcnow)

# Tabloları oluştur
Base.metadata.create_all(bind=engine)

# ===== ADMIN OLUŞTUR =====
with SessionLocal() as db:
    if not db.query(User).filter(User.kullanici_adi == "admin").first():
        admin = User(
            kullanici_adi="admin",
            email="admin@muys.com",
            sifre="admin123",
            adi="Admin",
            aktif=1
        )
        db.add(admin)
        db.commit()
        print("✅ Admin: admin / admin123")

# ===== UYGULAMA =====
app = FastAPI(title="MÜYS")
templates = Jinja2Templates(directory="app/templates")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ===== GİRİŞ =====
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login", response_class=HTMLResponse)
async def login_post(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    kullanici_adi = form.get("kullanici_adi")
    sifre = form.get("sifre")
    
    user = db.query(User).filter(
        User.kullanici_adi == kullanici_adi,
        User.sifre == sifre
    ).first()
    
    if user:
        return RedirectResponse(url="/", status_code=303)
    else:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "hata": "Hatalı kullanıcı adı veya şifre!"
        })

# ===== ANA SAYFA =====
@app.get("/", response_class=HTMLResponse)
async def index(request: Request, db: Session = Depends(get_db)):
    toplam_siparis = db.query(Siparis).count()
    toplam_musteri = db.query(Musteri).count()
    toplam_urun = db.query(Urun).count()
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "toplam_siparis": toplam_siparis,
        "toplam_musteri": toplam_musteri,
        "toplam_urun": toplam_urun
    })

# ===== MÜŞTERİLER =====
@app.get("/musteriler", response_class=HTMLResponse)
async def musteriler_page(request: Request, db: Session = Depends(get_db)):
    musteriler = db.query(Musteri).all()
    return templates.TemplateResponse("musteriler.html", {
        "request": request,
        "musteriler": musteriler
    })

@app.post("/musteri_ekle")
async def musteri_ekle(
    request: Request,
    db: Session = Depends(get_db)
):
    form = await request.form()
    musteri = Musteri(
        kodu=form.get("kodu"),
        adi=form.get("adi"),
        telefon=form.get("telefon"),
        email=form.get("email"),
        adres=form.get("adres")
    )
    db.add(musteri)
    db.commit()
    return {"durum": "başarılı", "mesaj": "Müşteri eklendi"}

# ===== ÜRÜNLER =====
@app.get("/urunler", response_class=HTMLResponse)
async def urunler_page(request: Request, db: Session = Depends(get_db)):
    urunler = db.query(Urun).all()
    return templates.TemplateResponse("urunler.html", {
        "request": request,
        "urunler": urunler
    })

@app.post("/urun_ekle")
async def urun_ekle(
    request: Request,
    db: Session = Depends(get_db)
):
    form = await request.form()
    urun = Urun(
        kodu=form.get("kodu"),
        adi=form.get("adi"),
        birim=form.get("birim", "Adet"),
        urun_tipi=form.get("urun_tipi", "Mamul"),
        mevcut_stok=float(form.get("mevcut_stok", 0)),
        min_stok=float(form.get("min_stok", 0)),
        birim_fiyat=float(form.get("birim_fiyat", 0))
    )
    db.add(urun)
    db.commit()
    return {"durum": "başarılı", "mesaj": "Ürün eklendi"}

# ===== DİĞER SAYFALAR =====
@app.get("/siparisler", response_class=HTMLResponse)
async def siparisler_page(request: Request):
    return templates.TemplateResponse("siparisler.html", {"request": request})

@app.get("/uretim", response_class=HTMLResponse)
async def uretim_page(request: Request):
    return templates.TemplateResponse("uretim.html", {"request": request})

@app.get("/stok", response_class=HTMLResponse)
async def stok_page(request: Request, db: Session = Depends(get_db)):
    urunler = db.query(Urun).all()
    return templates.TemplateResponse("stok.html", {
        "request": request,
        "urunler": urunler
    })

@app.get("/recete", response_class=HTMLResponse)
async def recete_page(request: Request):
    return templates.TemplateResponse("recete.html", {"request": request})

@app.get("/excel_import", response_class=HTMLResponse)
async def excel_import_page(request: Request):
    return templates.TemplateResponse("excel_import.html", {"request": request})

# ===== BAŞLAT =====
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
