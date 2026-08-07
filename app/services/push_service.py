import json
import base64
from datetime import datetime
from urllib.parse import urlparse

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.config import Config
from app.database import SessionLocal
from app.models.push_aboneligi import PushAboneligi
from app.models.vapid_ayari import VapidAyari


def _base64url(veri: bytes) -> str:
    return base64.urlsafe_b64encode(veri).rstrip(b"=").decode("ascii")


def _vapid_anahtarlari(db: Session, otomatik_olustur: bool = True) -> tuple[str, str, str]:
    if Config.VAPID_PUBLIC_KEY and Config.VAPID_PRIVATE_KEY:
        return Config.VAPID_PUBLIC_KEY, Config.VAPID_PRIVATE_KEY, Config.VAPID_SUBJECT
    ayar = db.query(VapidAyari).order_by(VapidAyari.id).first()
    if not ayar and otomatik_olustur:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import ec

        private = ec.generate_private_key(ec.SECP256R1())
        private_der = private.private_bytes(serialization.Encoding.DER, serialization.PrivateFormat.PKCS8, serialization.NoEncryption())
        public_point = private.public_key().public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
        ayar = VapidAyari(id=1, public_key=_base64url(public_point), private_key=_base64url(private_der), subject=Config.VAPID_SUBJECT or "mailto:admin@example.com")
        db.add(ayar)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            ayar = db.query(VapidAyari).filter(VapidAyari.id == 1).first()
    return (ayar.public_key, ayar.private_key, ayar.subject) if ayar else ("", "", "")


def push_yapilandirildi(db: Session) -> bool:
    return all(_vapid_anahtarlari(db))


def abonelik_durumu(db: Session, kullanici_id: int) -> dict:
    public_key, private_key, subject = _vapid_anahtarlari(db)
    return {
        "yapilandirildi": bool(public_key and private_key and subject),
        "aktif_abonelik": db.query(PushAboneligi).filter(PushAboneligi.kullanici_id == kullanici_id, PushAboneligi.aktif.is_(True)).count(),
        "public_key": public_key,
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
    public_key, private_key, subject = _vapid_anahtarlari(db)
    if not public_key or not private_key or not subject:
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
                vapid_private_key=private_key,
                vapid_claims={"sub": subject},
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
