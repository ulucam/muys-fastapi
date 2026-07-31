from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.auth import get_current_user

router = APIRouter(prefix="/api/uretim", tags=["uretim"])

@router.get("/")
def get_uretim(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return {"message": "Üretim sayfası", "rol": current_user.rol}
  
