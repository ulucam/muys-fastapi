from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import CariHareket, Musteri, User
from app.schemas import CariHareketCreate, CariHareketResponse
from app.auth import get_current_user

router = APIRouter(prefix="/api/cari", tags=["cari"])

@router.get("/musteri/{musteri_id}", response_model=List[CariHareketResponse])
def get_musteri_cari(musteri_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    musteri = db.query(Musteri).filter(Musteri.id == musteri_id).first()
    if not musteri:
        raise HTTPException(status_code=404, detail="Müşteri bulunamadı")
    
    return db.query(CariHareket).filter(CariHareket.musteri_id == musteri_id).order_by(CariHareket.created_at.desc()).all()

@router.post("/", response_model=CariHareketResponse, status_code=201)
def create_cari_hareket(hareket_data: CariHareketCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    musteri = db.query(Musteri).filter(Musteri.id == hareket_data.musteri_id).first()
    if not musteri:
        raise HTTPException(status_code=404, detail="Müşteri bulunamadı")
    
    new_hareket = CariHareket(**hareket_data.model_dump())
    db.add(new_hareket)
    db.commit()
    db.refresh(new_hareket)
    return new_hareket
