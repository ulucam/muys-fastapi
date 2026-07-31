from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import Musteri, User
from app.schemas import MusteriCreate, MusteriResponse
from app.auth import get_current_user

router = APIRouter(prefix="/api/musteriler", tags=["musteriler"])

@router.get("/", response_model=List[MusteriResponse])
def get_musteriler(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    musteriler = db.query(Musteri).order_by(Musteri.firma_adi).all()
    return musteriler

@router.post("/", response_model=MusteriResponse, status_code=status.HTTP_201_CREATED)
def create_musteri(
    musteri_data: MusteriCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Aynı kod var mı kontrol et
    existing = db.query(Musteri).filter(Musteri.firma_kodu == musteri_data.firma_kodu).first()
    if existing:
        raise HTTPException(status_code=400, detail="Bu firma kodu zaten kullanılıyor!")
    
    new_musteri = Musteri(**musteri_data.model_dump())
    db.add(new_musteri)
    db.commit()
    db.refresh(new_musteri)
    return new_musteri

@router.get("/{musteri_id}", response_model=MusteriResponse)
def get_musteri(
    musteri_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    musteri = db.query(Musteri).filter(Musteri.id == musteri_id).first()
    if not musteri:
        raise HTTPException(status_code=404, detail="Müşteri bulunamadı")
    return musteri

@router.put("/{musteri_id}", response_model=MusteriResponse)
def update_musteri(
    musteri_id: int,
    musteri_data: MusteriCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    musteri = db.query(Musteri).filter(Musteri.id == musteri_id).first()
    if not musteri:
        raise HTTPException(status_code=404, detail="Müşteri bulunamadı")
    
    for key, value in musteri_data.model_dump().items():
        setattr(musteri, key, value)
    
    db.commit()
    db.refresh(musteri)
    return musteri

@router.delete("/{musteri_id}")
def delete_musteri(
    musteri_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    musteri = db.query(Musteri).filter(Musteri.id == musteri_id).first()
    if not musteri:
        raise HTTPException(status_code=404, detail="Müşteri bulunamadı")
    
    db.delete(musteri)
    db.commit()
    return {"message": "Müşteri silindi"}
