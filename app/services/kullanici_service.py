from dataclasses import dataclass

from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.istasyon import Istasyon
from app.models.personel import Personel
from app.models.personel_istasyon import PersonelIstasyon
from app.models.rol_sinifi import RolSinifi
from app.models.user import User
from app.password import sifre_olustur


@dataclass(frozen=True)
class KullaniciSonucu:
    kullanici: User | None = None
    hata: str | None = None
    durum_kodu: int = 400


def form_secenekleri(db: Session, sadece_aktif: bool = True):
    istasyonlar, personeller = db.query(Istasyon), db.query(Personel)
    if sadece_aktif:
        istasyonlar = istasyonlar.filter(Istasyon.aktif.is_(True))
        personeller = personeller.filter(Personel.aktif.is_(True))
    return istasyonlar.order_by(Istasyon.kodu).all(), personeller.order_by(Personel.ad_soyad).all()


def personel_istasyon_secenekleri(db: Session):
    sonuc = {}
    atamalar = (db.query(PersonelIstasyon, Istasyon).join(Istasyon, Istasyon.id == PersonelIstasyon.istasyon_id)
        .filter(PersonelIstasyon.aktif.is_(True), Istasyon.aktif.is_(True)).order_by(Istasyon.kodu).all())
    for atama, istasyon in atamalar:
        sonuc.setdefault(atama.personel_id, []).append(f"{istasyon.kodu} · {istasyon.adi}")
    return sonuc


def rol_secenekleri(db: Session, aktor_rolu: str):
    aktor = db.query(RolSinifi).filter(RolSinifi.adi == aktor_rolu).first()
    seviye = aktor.seviye if aktor else -1
    return (db.query(RolSinifi).filter(RolSinifi.aktif.is_(True), RolSinifi.seviye <= seviye)
        .order_by(RolSinifi.seviye.desc(), RolSinifi.adi).all())


def atanabilir_personeller(db: Session, mevcut_kullanici_id: int | None = None):
    sorgu = db.query(Personel).outerjoin(User, User.personel_id == Personel.id).filter(Personel.aktif.is_(True))
    sorgu = sorgu.filter(or_(User.id.is_(None), User.id == mevcut_kullanici_id)) if mevcut_kullanici_id else sorgu.filter(User.id.is_(None))
    return sorgu.order_by(Personel.ad_soyad).all()


def kullanicilari_listele(db: Session):
    return db.query(User).filter(func.lower(User.kullanici_adi) != "admin").order_by(User.id.desc()).all()


def kullanici_getir(db: Session, kullanici_id: int):
    return db.query(User).filter(User.id == kullanici_id).first()


def _rol_atanabilir(db: Session, aktor_rolu: str, hedef_rolu: str):
    aktor = db.query(RolSinifi).filter(RolSinifi.adi == aktor_rolu, RolSinifi.aktif.is_(True)).first()
    hedef = db.query(RolSinifi).filter(RolSinifi.adi == hedef_rolu, RolSinifi.aktif.is_(True)).first()
    return bool(aktor and hedef and hedef.seviye <= aktor.seviye)


def _operator_istasyonlari(db: Session, rol: str, personel_id: int):
    if rol != "Operatör":
        return []
    return (db.query(Istasyon).join(PersonelIstasyon, PersonelIstasyon.istasyon_id == Istasyon.id)
        .filter(PersonelIstasyon.personel_id == personel_id, PersonelIstasyon.aktif.is_(True), Istasyon.aktif.is_(True))
        .order_by(Istasyon.kodu).all())


def _personel_dogrula(db: Session, personel_id: int | None, haric_id: int | None = None):
    personel = db.query(Personel).filter(Personel.id == personel_id, Personel.aktif.is_(True)).first() if personel_id else None
    sorgu = db.query(User).filter(User.personel_id == personel_id) if personel_id else None
    if sorgu is not None and haric_id:
        sorgu = sorgu.filter(User.id != haric_id)
    return personel if personel and not (sorgu.first() if sorgu is not None else None) else None


def kullanici_olustur(db: Session, aktor_rolu: str, **veri):
    kullanici_adi, email, rol = veri["kullanici_adi"].strip(), veri.get("email", "").strip() or None, veri["rol"]
    if not _rol_atanabilir(db, aktor_rolu, rol):
        return KullaniciSonucu(hata="Kendi yetki seviyenizden yüksek bir rol atayamazsınız.", durum_kodu=403)
    personel = _personel_dogrula(db, veri.get("personel_id"))
    if not personel:
        return KullaniciSonucu(hata="Başka hesaba atanmamış aktif bir personel seçmelisiniz.")
    istasyonlar = _operator_istasyonlari(db, rol, personel.id)
    if rol == "Operatör" and not istasyonlar:
        return KullaniciSonucu(hata="Operatör personeline önce en az bir istasyon atanmalıdır.")
    if db.query(User).filter(func.lower(User.kullanici_adi) == kullanici_adi.casefold()).first():
        return KullaniciSonucu(hata="Bu kullanıcı adı zaten kayıtlı.")
    if email and db.query(User).filter(func.lower(User.email) == email.casefold()).first():
        return KullaniciSonucu(hata="Bu e-posta adresi başka bir kullanıcıda kayıtlı.")
    kullanici = User(kullanici_adi=kullanici_adi, sifre=sifre_olustur(veri["sifre"]), ad_soyad=personel.ad_soyad,
        telefon=veri.get("telefon", ""), email=email, rol=rol, aktif=veri.get("aktif", True), personel_id=personel.id,
        istasyon_id=istasyonlar[0].id if istasyonlar else None)
    try:
        db.add(kullanici); db.commit()
        return KullaniciSonucu(kullanici=kullanici)
    except IntegrityError:
        db.rollback(); return KullaniciSonucu(hata="Kullanıcı kaydedilemedi; kullanıcı adı veya e-posta kullanılıyor.")


def kullanici_guncelle(db: Session, kullanici_id: int, aktor_rolu: str, **veri):
    kullanici = kullanici_getir(db, kullanici_id)
    if not kullanici:
        return KullaniciSonucu()
    rol = veri["rol"]
    if not _rol_atanabilir(db, aktor_rolu, kullanici.rol) or not _rol_atanabilir(db, aktor_rolu, rol):
        return KullaniciSonucu(kullanici=kullanici, hata="Kendi seviyenizden yüksek kullanıcıyı düzenleyemez veya rol atayamazsınız.", durum_kodu=403)
    personel = _personel_dogrula(db, veri.get("personel_id"), kullanici_id)
    if not personel:
        return KullaniciSonucu(kullanici=kullanici, hata="Başka hesaba atanmamış aktif bir personel seçmelisiniz.")
    istasyonlar = _operator_istasyonlari(db, rol, personel.id)
    if rol == "Operatör" and not istasyonlar:
        return KullaniciSonucu(kullanici=kullanici, hata="Operatör personeline önce en az bir istasyon atanmalıdır.")
    kullanici_adi, email = veri["kullanici_adi"].strip(), veri.get("email", "").strip() or None
    if db.query(User).filter(func.lower(User.kullanici_adi) == kullanici_adi.casefold(), User.id != kullanici_id).first():
        return KullaniciSonucu(kullanici=kullanici, hata="Bu kullanıcı adı başka bir kullanıcıda kayıtlı.")
    kullanici.kullanici_adi, kullanici.ad_soyad, kullanici.telefon = kullanici_adi, personel.ad_soyad, veri.get("telefon", "")
    kullanici.email, kullanici.rol, kullanici.aktif, kullanici.personel_id = email, rol, veri.get("aktif", True), personel.id
    kullanici.istasyon_id = istasyonlar[0].id if istasyonlar else None
    if veri.get("sifre", "").strip():
        kullanici.sifre = sifre_olustur(veri["sifre"])
    try:
        db.commit(); return KullaniciSonucu(kullanici=kullanici)
    except IntegrityError:
        db.rollback(); return KullaniciSonucu(kullanici=kullanici, hata="Kullanıcı kaydedilemedi; bilgiler çakışıyor.")


def kullanici_sil(db: Session, kullanici_id: int):
    kullanici = kullanici_getir(db, kullanici_id)
    if kullanici:
        db.delete(kullanici); db.commit()
