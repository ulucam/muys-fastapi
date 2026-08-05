from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import User
from app.schemas import UrunCreate, UrunResponse
from app.auth import get_current_user
from app.services.urun_service import urun_olustur, urunleri_listele

router = APIRouter(prefix="/api/urunler", tags=["urunler"])

@router.get("/", response_model=List[UrunResponse])
def get_urunler(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return urunleri_listele(db)

@router.post("/", response_model=UrunResponse, status_code=status.HTTP_201_CREATED)
def create_urun(urun_data: UrunCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    urun = urun_olustur(db, urun_data)
    if not urun:
        raise HTTPException(status_code=400, detail="Bu ürün kodu zaten kullanılıyor!")
    return urun
