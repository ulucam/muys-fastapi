from pydantic import BaseModel, EmailStr
from datetime import datetime, date
from typing import Optional, List

class UserBase(BaseModel):
    kullanici_adi: str
    email: EmailStr
    adi: Optional[str] = None
    soyadi: Optional[str] = None
    rol: str = "Operator"

class UserCreate(UserBase):
    sifre: str

class UserLogin(BaseModel):
    kullanici_adi: str
    sifre: str

class UserResponse(UserBase):
    id: int
    aktif: bool
    created_at: datetime
    class Config:
        from_attributes = True

class MusteriBase(BaseModel):
    firma_kodu: str
    firma_adi: str
    yetkili: Optional[str] = None
    telefon: Optional[str] = None
    email: Optional[str] = None
    il: Optional[str] = None
    ilce: Optional[str] = None
    acik_adres: Optional[str] = None
    vergi_no: Optional[str] = None
    musteri_tipi: str = "Alıcı"
    odeme_tipi: str = "Vadeli"

class MusteriCreate(MusteriBase):
    pass

class MusteriResponse(MusteriBase):
    id: int
    bakiye: float
    toplam_borc: float
    toplam_alacak: float
    created_at: datetime
    class Config:
        from_attributes = True

class UrunBase(BaseModel):
    kodu: str
    adi: str
    birim: str = "Adet"
    urun_tipi: str = "Mamul"
    mevcut_stok: float = 0
    min_stok: float = 0
    birim_fiyat: float = 0

class UrunCreate(UrunBase):
    pass

class UrunResponse(UrunBase):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True

class SiparisKalemBase(BaseModel):
    urun_id: int
    miktar: float
    birim_fiyat: Optional[float] = 0

class SiparisCreate(BaseModel):
    siparis_no: str
    musteri_id: int
    teslim_tarihi: Optional[date] = None
    notlar: Optional[str] = None
    kalemler: List[SiparisKalemBase]

class SiparisResponse(BaseModel):
    id: int
    siparis_no: str
    musteri_id: int
    musteri_adi: str
    siparis_tarihi: datetime
    teslim_tarihi: Optional[date]
    durum: str
    notlar: Optional[str]
    toplam_tutar: float
    class Config:
        from_attributes = True

class CariHareketCreate(BaseModel):
    musteri_id: int
    hareket_tipi: str
    tutar: float
    aciklama: Optional[str] = None
    referans_no: Optional[str] = None
    vade_tarihi: Optional[date] = None

class CariHareketResponse(BaseModel):
    id: int
    musteri_id: int
    hareket_tipi: str
    tutar: float
    borc: float
    alacak: float
    aciklama: Optional[str]
    referans_no: Optional[str]
    odeme_durumu: str
    created_at: datetime
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse
