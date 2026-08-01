from fastapi import FastAPI, Depends, HTTPException, status, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import List

from app.config import Config
from app.database import get_db, engine, Base
from app.models import Rol, User, Musteri, Urun, Siparis, SiparisKalem
from app.schemas import UserCreate, UserLogin, Token, MusteriCreate, UrunCreate, SiparisCreate
from app.auth import (
    authenticate_user, create_access_token, get_current_user, 
    get_current_active_user, get_password_hash, oauth2_scheme
)

# ===== UYGULAMA =====
app = FastAPI(title="MÜYS - Mysto Üretim Yönetim Sistemi", version="1.0.0")

# ===== ŞABLONLAR =====
templates = Jinja2Templates(directory="app/templates")

# ===== VERİTABANINI OLUŞTUR =====
Base.metadata.create_all(bind=engine)

# ===== ROUTES =====
@app.get("/", response_class=HTMLResponse)
async def index(request: Request, current_user: User = Depends(get_current_user)):
    return templates.TemplateResponse("index.html", {"request": request, "user": current_user})

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Hatalı kullanıcı adı veya şifre!",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=Config.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.kullanici_adi}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/logout")
async def logout():
    return RedirectResponse(url="/login")

# ===== MÜŞTERİLER =====
@app.get("/musteriler", response_class=HTMLResponse)
async def musteriler_page(request: Request, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    musteriler = db.query(Musteri).all()
    return templates.TemplateResponse("musteriler.html", {"request": request, "musteriler": musteriler, "user": current_user})

@app.post("/musteri_ekle")
async def musteri_ekle(musteri: MusteriCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_musteri = Musteri(**musteri.model_dump())
    db.add(db_musteri)
    db.commit()
    db.refresh(db_musteri)
    return {"durum": "başarılı", "mesaj": "Müşteri eklendi", "id": db_musteri.id}

# ===== ÜRÜNLER =====
@app.get("/urunler", response_class=HTMLResponse)
async def urunler_page(request: Request, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    urunler = db.query(Urun).all()
    return templates.TemplateResponse("urunler.html", {"request": request, "urunler": urunler, "user": current_user})

@app.post("/urun_ekle")
async def urun_ekle(urun: UrunCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_urun = Urun(**urun.model_dump())
    db.add(db_urun)
    db.commit()
    db.refresh(db_urun)
    return {"durum": "başarılı", "mesaj": "Ürün eklendi", "id": db_urun.id}

# ===== SİPARİŞLER =====
@app.get("/siparisler", response_class=HTMLResponse)
async def siparisler_page(request: Request, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    siparisler = db.query(Siparis).all()
    musteriler = db.query(Musteri).all()
    urunler = db.query(Urun).all()
    return templates.TemplateResponse("siparisler.html", {"request": request, "siparisler": siparisler, "musteriler": musteriler, "urunler": urunler, "user": current_user})

@app.post("/siparis_ekle")
async def siparis_ekle(siparis: SiparisCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_siparis = Siparis(
        siparis_no=siparis.siparis_no,
        musteri_id=siparis.musteri_id,
        teslim_tarihi=siparis.teslim_tarihi,
        notlar=siparis.notlar
    )
    db.add(db_siparis)
    db.commit()
    db.refresh(db_siparis)
    
    for kalem in siparis.kalemler:
        db_kalem = SiparisKalem(
            siparis_id=db_siparis.id,
            urun_id=kalem.urun_id,
            miktar=kalem.miktar
        )
        db.add(db_kalem)
    
    db.commit()
    return {"durum": "başarılı", "mesaj": f"Sipariş {siparis.siparis_no} eklendi", "id": db_siparis.id}

# ===== ÜRETİM =====
@app.get("/uretim", response_class=HTMLResponse)
async def uretim_page(request: Request, current_user: User = Depends(get_current_user)):
    return templates.TemplateResponse("uretim.html", {"request": request, "user": current_user})

# ===== STOK =====
@app.get("/stok", response_class=HTMLResponse)
async def stok_page(request: Request, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    urunler = db.query(Urun).all()
    return templates.TemplateResponse("stok.html", {"request": request, "urunler": urunler, "user": current_user})

# ===== REÇETE =====
@app.get("/recete", response_class=HTMLResponse)
async def recete_page(request: Request, current_user: User = Depends(get_current_user)):
    return templates.TemplateResponse("recete.html", {"request": request, "user": current_user})

# ===== EXCEL İMPORT =====
@app.get("/excel_import", response_class=HTMLResponse)
async def excel_import_page(request: Request, current_user: User = Depends(get_current_user)):
    return templates.TemplateResponse("excel_import.html", {"request": request, "user": current_user})

# ===== BAŞLAT =====
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
