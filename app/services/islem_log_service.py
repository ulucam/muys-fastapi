from datetime import datetime, timedelta

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


def son_kullanici_hareketleri(db: Session, saniye: int = 60, limit: int = 8) -> list[dict]:
    """Son süre içindeki yetkili kullanıcı hareketlerini başlık bildirimi için döndürür."""
    baslangic = datetime.utcnow() - timedelta(seconds=saniye)
    kayitlar = (
        db.query(IslemLogu, User.rol)
        .join(User, User.kullanici_adi == IslemLogu.kullanici_adi)
        .filter(
            User.rol.in_(["Admin", "Yönetici", "Operatör"]),
            IslemLogu.created_at >= baslangic,
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
        }
        for log, rol in kayitlar
    ]
