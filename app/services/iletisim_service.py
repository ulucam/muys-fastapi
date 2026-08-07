from datetime import datetime

from sqlalchemy.orm import Session

from app.models.bildirim import Bildirim
from app.models.mesaj import Mesaj
from app.models.user import User


def aktif_kullanicilar(db: Session, haric_id: int):
    return db.query(User).filter(User.aktif.is_(True), User.id != haric_id).order_by(User.ad_soyad).all()


def bildirim_olustur(db: Session, kullanici_id: int, baslik: str, mesaj: str, tur: str = "bilgi", baglanti: str = ""):
    bildirim = Bildirim(kullanici_id=kullanici_id, baslik=baslik[:120], mesaj=mesaj[:500], tur=tur[:30], baglanti=baglanti[:300])
    db.add(bildirim)
    return bildirim


def mesaj_gonder(db: Session, gonderen_id: int, alici_id: int, konu: str, icerik: str):
    konu, icerik = konu.strip(), icerik.strip()
    alici = db.query(User).filter(User.id == alici_id, User.aktif.is_(True)).first()
    gonderen = db.query(User).filter(User.id == gonderen_id, User.aktif.is_(True)).first()
    if not alici or not gonderen or alici.id == gonderen.id:
        raise ValueError("Geçerli bir alıcı seçin")
    if not konu or not icerik or len(konu) > 150 or len(icerik) > 5000:
        raise ValueError("Konu ve mesaj zorunludur; mesaj en fazla 5000 karakter olabilir")
    mesaj = Mesaj(gonderen_id=gonderen.id, alici_id=alici.id, konu=konu, icerik=icerik)
    db.add(mesaj)
    db.flush()
    bildirim_olustur(db, alici.id, "Yeni mesaj", f"{gonderen.ad_soyad} size bir mesaj gönderdi: {konu}", "mesaj", f"/mesajlar#mesaj-{mesaj.id}")
    db.commit()
    return mesaj


def mesaj_kutulari(db: Session, kullanici_id: int) -> dict:
    kullanicilar = {k.id: k for k in db.query(User).all()}
    gelen = db.query(Mesaj).filter(Mesaj.alici_id == kullanici_id, Mesaj.alici_sildi.is_(False)).order_by(Mesaj.created_at.desc()).limit(200).all()
    giden = db.query(Mesaj).filter(Mesaj.gonderen_id == kullanici_id, Mesaj.gonderen_sildi.is_(False)).order_by(Mesaj.created_at.desc()).limit(200).all()
    return {"gelen": gelen, "giden": giden, "kullanicilar": kullanicilar, "okunmamis": sum(not mesaj.okundu for mesaj in gelen)}


def mesaji_okundu_yap(db: Session, mesaj_id: int, kullanici_id: int) -> bool:
    mesaj = db.query(Mesaj).filter(Mesaj.id == mesaj_id, Mesaj.alici_id == kullanici_id, Mesaj.alici_sildi.is_(False)).first()
    if not mesaj:
        return False
    if not mesaj.okundu:
        mesaj.okundu, mesaj.okunma_tarihi = True, datetime.utcnow()
        db.commit()
    return True


def bildirimleri_okundu_yap(db: Session, kullanici_id: int) -> int:
    bildirimler = db.query(Bildirim).filter(Bildirim.kullanici_id == kullanici_id, Bildirim.okundu.is_(False)).all()
    simdi = datetime.utcnow()
    for bildirim in bildirimler:
        bildirim.okundu, bildirim.okunma_tarihi = True, simdi
    db.commit()
    return len(bildirimler)


def iletisim_ozeti(db: Session, kullanici_id: int) -> dict:
    bildirimler = db.query(Bildirim).filter(Bildirim.kullanici_id == kullanici_id).order_by(Bildirim.created_at.desc()).limit(8).all()
    okunmamis_bildirim = db.query(Bildirim).filter(Bildirim.kullanici_id == kullanici_id, Bildirim.okundu.is_(False)).count()
    okunmamis_mesaj = db.query(Mesaj).filter(Mesaj.alici_id == kullanici_id, Mesaj.okundu.is_(False), Mesaj.alici_sildi.is_(False)).count()
    return {
        "okunmamis_bildirim": okunmamis_bildirim,
        "okunmamis_mesaj": okunmamis_mesaj,
        "bildirimler": [{
            "id": b.id, "baslik": b.baslik, "mesaj": b.mesaj, "tur": b.tur, "baglanti": b.baglanti,
            "okundu": b.okundu, "zaman": b.created_at.strftime("%d.%m.%Y %H:%M"),
        } for b in bildirimler],
    }
