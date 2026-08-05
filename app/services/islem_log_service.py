from fastapi import Request
from sqlalchemy.orm import Session

from app.models.islem_logu import IslemLogu


def islem_logla(db: Session, request: Request, modul: str, islem: str, detay: str = "", commit: bool = False):
    db.add(IslemLogu(
        kullanici_adi=request.session.get("kullanici_adi", "Sistem"),
        modul=modul,
        islem=islem,
        detay=detay,
        ip_adresi=request.client.host if request.client else "",
    ))
    if commit:
        db.commit()
