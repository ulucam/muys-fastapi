from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import Urun, User
from app.schemas import UrunCreate, UrunResponse
from app.auth import get_current_user

router = APIRouter(prefix="/api/urunler", tags=["urunler"])

@router.get("/", response_model=List[UrunResponse])
def get_urunler(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Urun).order_by(Urun.adi).all()

@router.post("/", response_model=UrunResponse, status_code=status.HTTP_201_CREATED)
def create_urun(urun_data: UrunCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    existing = db.query(Urun).filter(Urun.kodu == urun_data.kodu).first()
    if existing:
        raise HTTPException(status_code=400, detail="Bu ürün kodu zaten kullanılıyor!")
    
    new_urun = Urun(**urun_data.model_dump())
    db.add(new_urun)
    db.commit()
    db.refresh(new_urun)
    return new_urun
