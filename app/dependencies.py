"""Ortak kullanılan Depends() fonksiyonları.

Rol kontrolü ve kullanıcı yönetimi yetki denetimleri burada toplanır.
``app.security`` bu modüldeki fonksiyonları geriye uyumluluk için
yeniden dışa aktarır.
"""

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.rol_sinifi import RolSinifi


def yetki_kontrol(izinli_roller):
    """Rolü ``izinli_roller`` içinde olmayan istekleri 403 ile reddeder."""

    def kontrol(request: Request):
        rol = request.session.get("rol", "")
        if rol not in izinli_roller:
            raise HTTPException(status_code=403, detail="Bu sayfaya erişim yetkiniz yok.")
        return True

    return kontrol


def kullanici_yonetim_kontrol(request: Request, db: Session = Depends(get_db)):
    """Admin veya rolüne Admin tarafından kullanıcı ekleme izni verilmiş kullanıcı."""
    rol_adi = request.session.get("rol", "")
    rol = db.query(RolSinifi).filter(RolSinifi.adi == rol_adi, RolSinifi.aktif.is_(True)).first()
    if rol_adi != "Admin" and (not rol or not rol.kullanici_ekleyebilir):
        raise HTTPException(status_code=403, detail="Kullanıcı yönetimi yetkiniz yok.")
    return rol
