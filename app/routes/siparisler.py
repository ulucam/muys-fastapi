from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import Siparis, SiparisKalem, Urun, Musteri, User
from app.schemas import SiparisCreate, SiparisResponse
from app.auth import get_current_user

router = APIRouter(prefix="/api/siparisler", tags=["siparisler"])

@router.get("/", response_model=List[SiparisResponse])
def get_siparisler(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    siparisler = db.query(Siparis).order_by(Siparis.created_at.desc()).all()
    result = []
    for s in siparisler:
        toplam = sum(k.miktar * (k.birim_fiyat or 0) for k in s.kalemler)
        result.append({
            "id": s.id,
            "siparis_no": s.siparis_no,
            "musteri_id": s.musteri_id,
            "musteri_adi": s.musteri.firma_adi if s.musteri else "-",
            "siparis_tarihi": s.siparis_tarihi,
            "teslim_tarihi": s.teslim_tarihi,
            "durum": s.durum,
            "notlar": s.notlar,
            "toplam_tutar": toplam
        })
    return result

@router.post("/", response_model=SiparisResponse, status_code=status.HTTP_201_CREATED)
def create_siparis(siparis_data: SiparisCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    existing = db.query(Siparis).filter(Siparis.siparis_no == siparis_data.siparis_no).first()
    if existing:
        raise HTTPException(status_code=400, detail="Bu sipariş no zaten kullanılıyor!")
    
    musteri = db.query(Musteri).filter(Musteri.id == siparis_data.musteri_id).first()
    if not musteri:
        raise HTTPException(status_code=404, detail="Müşteri bulunamadı!")
    
    new_siparis = Siparis(
        siparis_no=siparis_data.siparis_no,
        musteri_id=siparis_data.musteri_id,
        teslim_tarihi=siparis_data.teslim_tarihi,
        notlar=siparis_data.notlar,
        durum="Beklemede"
    )
    db.add(new_siparis)
    db.flush()
    
    toplam_tutar = 0
    for kalem_data in siparis_data.kalemler:
        urun = db.query(Urun).filter(Urun.id == kalem_data.urun_id).first()
        if not urun:
            raise HTTPException(status_code=404, detail=f"Ürün ID {kalem_data.urun_id} bulunamadı!")
        
        birim_fiyat = kalem_data.birim_fiyat or urun.birim_fiyat or 0
        satir_toplam = kalem_data.miktar * birim_fiyat
        toplam_tutar += satir_toplam
        
        kalem = SiparisKalem(
            siparis_id=new_siparis.id,
            urun_id=kalem_data.urun_id,
            miktar=kalem_data.miktar,
            birim_fiyat=birim_fiyat,
            toplam_tutar=satir_toplam
        )
        db.add(kalem)
    
    db.commit()
    db.refresh(new_siparis)
    
    return {
        "id": new_siparis.id,
        "siparis_no": new_siparis.siparis_no,
        "musteri_id": new_siparis.musteri_id,
        "musteri_adi": musteri.firma_adi,
        "siparis_tarihi": new_siparis.siparis_tarihi,
        "teslim_tarihi": new_siparis.teslim_tarihi,
        "durum": new_siparis.durum,
        "notlar": new_siparis.notlar,
        "toplam_tutar": toplam_tutar
    }
