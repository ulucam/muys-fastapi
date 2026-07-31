from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Siparis, Urun, Musteri, User
from app.auth import get_current_user

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

@router.get("/")
def get_dashboard(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    toplam_siparis = db.query(Siparis).count()
    aktif_siparis = db.query(Siparis).filter(Siparis.durum.in_(['Beklemede', 'Onaylandi', 'Uretimde'])).count()
    tamamlanan_siparis = db.query(Siparis).filter(Siparis.durum == 'Tamamlandi').count()
    bekleyen_siparis = db.query(Siparis).filter(Siparis.durum == 'Beklemede').count()
    kritik_stok = db.query(Urun).filter(Urun.mevcut_stok <= Urun.min_stok, Urun.min_stok > 0).count()
    toplam_musteri = db.query(Musteri).count()
    toplam_urun = db.query(Urun).count()
    
    return {
        "toplam_siparis": toplam_siparis,
        "aktif_siparis": aktif_siparis,
        "tamamlanan_siparis": tamamlanan_siparis,
        "bekleyen_siparis": bekleyen_siparis,
        "kritik_stok": kritik_stok,
        "toplam_musteri": toplam_musteri,
        "toplam_urun": toplam_urun,
        "rol": current_user.rol
    }
