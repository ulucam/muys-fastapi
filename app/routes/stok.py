from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import Urun, User
from app.schemas import UrunResponse
from app.auth import get_current_user

router = APIRouter(prefix="/api/stok", tags=["stok"])

@router.get("/", response_model=List[UrunResponse])
def get_stok(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Urun).order_by(Urun.adi).all()
