from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import User
from app.schemas import SiparisCreate, SiparisResponse
from app.auth import get_current_user
from app.services.siparis_service import SiparisHatasi, siparis_olustur, siparisleri_listele

router = APIRouter(prefix="/api/siparisler", tags=["siparisler"])

@router.get("/", response_model=List[SiparisResponse])
def get_siparisler(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return siparisleri_listele(db)

@router.post("/", response_model=SiparisResponse, status_code=status.HTTP_201_CREATED)
def create_siparis(siparis_data: SiparisCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        return siparis_olustur(db, siparis_data)
    except SiparisHatasi as hata:
        raise HTTPException(status_code=hata.durum_kodu, detail=hata.mesaj) from hata
