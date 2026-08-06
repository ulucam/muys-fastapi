from datetime import datetime

from fastapi import Request
from sqlalchemy.orm import Session

from app.models.islem_logu import IslemLogu
from app.models.user import User


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


def son_kullanici_hareketleri(db: Session, limit: int = 5) -> list[dict]:
    """Başlıktaki açılır liste için son kullanıcı hareketlerini döndürür."""
    simdi = datetime.utcnow()
    kayitlar = (
        db.query(IslemLogu, User.rol)
        .join(User, User.kullanici_adi == IslemLogu.kullanici_adi)
        .filter(
            User.rol.in_(["Admin", "Yönetici", "Operatör"]),
        )
        .order_by(IslemLogu.created_at.desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "kullanici_adi": log.kullanici_adi,
            "rol": rol,
            "modul": log.modul,
            "islem": log.islem,
            "zaman": log.created_at.strftime("%H:%M:%S"),
            "yas_saniye": max(0, int((simdi - log.created_at).total_seconds())),
        }
        for log, rol in kayitlar
    ]
