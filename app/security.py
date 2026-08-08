from fastapi import Depends, Request, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.rol_sinifi import RolSinifi


def yetki_kontrol(izinli_roller):

    def kontrol(request: Request):

        rol = request.session.get(
            "rol",
            ""
        )


        if rol not in izinli_roller:

            raise HTTPException(
                status_code=403,
                detail="Bu sayfaya erişim yetkiniz yok."
            )


        return True


    return kontrol


def kullanici_yonetim_kontrol(request: Request, db: Session = Depends(get_db)):
    """Admin veya rolüne Admin tarafından kullanıcı ekleme izni verilmiş kullanıcı."""
    rol_adi = request.session.get("rol", "")
    rol = db.query(RolSinifi).filter(RolSinifi.adi == rol_adi, RolSinifi.aktif.is_(True)).first()
    if rol_adi != "Admin" and (not rol or not rol.kullanici_ekleyebilir):
        raise HTTPException(status_code=403, detail="Kullanıcı yönetimi yetkiniz yok.")
    return rol


def yedekleme_kontrol(request: Request, db: Session = Depends(get_db)):
    """Admin veya Admin'in yedek/Excel aktarım izni verdiği rol."""
    rol_adi = request.session.get("rol", "")
    rol = db.query(RolSinifi).filter(RolSinifi.adi == rol_adi, RolSinifi.aktif.is_(True)).first()
    if rol_adi != "Admin" and (not rol or not rol.yedekleme_yapabilir):
        raise HTTPException(status_code=403, detail="Yedekleme ve Excel aktarımı yetkiniz yok.")
    return rol


def kendi_loglarini_gorme_kontrol(request: Request, db: Session = Depends(get_db)):
    rol_adi = request.session.get("rol", "")
    rol = db.query(RolSinifi).filter(RolSinifi.adi == rol_adi, RolSinifi.aktif.is_(True)).first()
    if not request.session.get("user_id") or (rol_adi != "Admin" and (not rol or not rol.loglarini_gorebilir)):
        raise HTTPException(status_code=403, detail="İşlem geçmişinizi görüntüleme yetkiniz yok.")
    return rol
