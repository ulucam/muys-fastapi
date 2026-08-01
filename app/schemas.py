from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List

# ===== KULLANICI =====
class UserBase(BaseModel):
    kullanici_adi: str
    email: EmailStr
    adi: Optional[str] = None
    soyadi: Optional[str] = None
    telefon: Optional[str] = None

class UserCreate(UserBase):
    sifre: str

class UserLogin(BaseModel):
    kullanici_adi: str
    sifre: str

class UserResponse(UserBase):
    id: int
    rol_id: int
    aktif: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# ===== MÜŞTERİ =====
class MusteriBase(BaseModel):
    kodu: str
    adi: str
    telefon: Optional[str] = None
    email: Optional[str] = None
    adres: Optional[str] = None
    vergi_no: Optional[str] = None

class MusteriCreate(MusteriBase):
    pass

class MusteriResponse(MusteriBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# ===== ÜRÜN =====
class UrunBase(BaseModel):
    kodu: str
    adi: str
    aciklama: Optional[str] = None
    birim: Optional[str] = "Adet"
    urun_tipi: Optional[str] = "Mamul"
    tahmini_uretim_suresi: Optional[float] = 0
    min_stok: Optional[float] = 0
    mevcut_stok: Optional[float] = 0
    birim_fiyat: Optional[float] = 0
    malzeme: Optional[str] = None
    kalinlik: Optional[float] = None

class UrunCreate(UrunBase):
    pass

class UrunResponse(UrunBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# ===== SİPARİŞ =====
class SiparisKalemBase(BaseModel):
    urun_id: int
    miktar: float

class SiparisKalemCreate(SiparisKalemBase):
    pass

class SiparisKalemResponse(SiparisKalemBase):
    id: int
    uretilen_miktar: float
    durum: str
    
    class Config:
        from_attributes = True

class SiparisBase(BaseModel):
    siparis_no: str
    musteri_id: int
    teslim_tarihi: Optional[datetime] = None
    notlar: Optional[str] = None

class SiparisCreate(SiparisBase):
    kalemler: List[SiparisKalemCreate]

class SiparisResponse(SiparisBase):
    id: int
    durum: str
    created_at: datetime
    kalemler: List[SiparisKalemResponse]
    
    class Config:
        from_attributes = True

# ===== TOKEN =====
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    kullanici_adi: Optional[str] = None
