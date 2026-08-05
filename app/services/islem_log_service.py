from fastapi import Request
from sqlalchemy.orm import Session

from app.models.islem_logu import IslemLogu


def islem_logla(db: Session, request: Request, modul: str, islem: str, detay: str = "", commit: bool = False):
    islem_logla_veri(
        db,
        request.session.get("kullanici_adi", "Sistem"),
        request.client.host if request.client else "",
        modul,
        islem,
        detay,
        commit,
    )


def islem_logla_veri(
    db: Session,
    kullanici_adi: str,
    ip_adresi: str,
    modul: str,
    islem: str,
    detay: str = "",
    commit: bool = False,
):
    db.add(IslemLogu(
        kullanici_adi=kullanici_adi,
        modul=modul,
        islem=islem,
        detay=detay,
        ip_adresi=ip_adresi,
    ))
    if commit:
        db.commit()
