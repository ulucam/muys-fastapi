import json
from datetime import datetime
from urllib.parse import urlparse

from sqlalchemy.orm import Session

from app.config import Config
from app.database import SessionLocal
from app.models.push_aboneligi import PushAboneligi


def push_yapilandirildi() -> bool:
    return bool(Config.VAPID_PUBLIC_KEY and Config.VAPID_PRIVATE_KEY and Config.VAPID_SUBJECT)


def abonelik_durumu(db: Session, kullanici_id: int) -> dict:
    return {
        "yapilandirildi": push_yapilandirildi(),
        "aktif_abonelik": db.query(PushAboneligi).filter(PushAboneligi.kullanici_id == kullanici_id, PushAboneligi.aktif.is_(True)).count(),
        "public_key": Config.VAPID_PUBLIC_KEY if push_yapilandirildi() else "",
    }


def abonelik_kaydet(db: Session, kullanici_id: int, veri: dict, cihaz_adi: str = ""):
    endpoint = str(veri.get("endpoint") or "").strip()
    anahtarlar = veri.get("keys") if isinstance(veri.get("keys"), dict) else {}
    p256dh, auth = str(anahtarlar.get("p256dh") or "").strip(), str(anahtarlar.get("auth") or "").strip()
    parsed = urlparse(endpoint)
    if parsed.scheme != "https" or not parsed.netloc or len(endpoint) > 1000 or not p256dh or not auth:
        raise ValueError("Geçersiz push aboneliği")
    abonelik = db.query(PushAboneligi).filter(PushAboneligi.endpoint == endpoint).first()
    if not abonelik:
        abonelik = PushAboneligi(endpoint=endpoint)
    abonelik.kullanici_id, abonelik.p256dh_key, abonelik.auth_key = kullanici_id, p256dh[:300], auth[:300]
    abonelik.cihaz_adi, abonelik.aktif, abonelik.son_kullanim = cihaz_adi[:200], True, datetime.utcnow()
    db.add(abonelik)
    db.commit()
    return abonelik


def abonelik_sil(db: Session, kullanici_id: int, endpoint: str) -> bool:
    abonelik = db.query(PushAboneligi).filter(PushAboneligi.kullanici_id == kullanici_id, PushAboneligi.endpoint == endpoint).first()
    if not abonelik:
        return False
    abonelik.aktif = False
    db.commit()
    return True


def _push_gonder(db: Session, kullanici_id: int, baslik: str, icerik: str, baglanti: str, badge: int | None = None) -> int:
    if not push_yapilandirildi():
        return 0
    from pywebpush import WebPushException, webpush

    abonelikler = db.query(PushAboneligi).filter(PushAboneligi.kullanici_id == kullanici_id, PushAboneligi.aktif.is_(True)).all()
    payload = json.dumps({"title": baslik[:120], "body": icerik[:500], "url": baglanti or "/", "badge": badge}, ensure_ascii=False)
    gonderilen = 0
    for abonelik in abonelikler:
        try:
            webpush(
                subscription_info={"endpoint": abonelik.endpoint, "keys": {"p256dh": abonelik.p256dh_key, "auth": abonelik.auth_key}},
                data=payload,
                vapid_private_key=Config.VAPID_PRIVATE_KEY,
                vapid_claims={"sub": Config.VAPID_SUBJECT},
                timeout=10,
            )
            abonelik.son_kullanim = datetime.utcnow()
            gonderilen += 1
        except WebPushException as hata:
            durum = getattr(getattr(hata, "response", None), "status_code", None)
            if durum in (404, 410):
                abonelik.aktif = False
        except Exception:
            continue
    db.commit()
    return gonderilen


def arka_planda_push_gonder(kullanici_id: int, baslik: str, icerik: str, baglanti: str = "/", badge: int | None = None) -> int:
    db = SessionLocal()
    try:
        return _push_gonder(db, kullanici_id, baslik, icerik, baglanti, badge)
    finally:
        db.close()
