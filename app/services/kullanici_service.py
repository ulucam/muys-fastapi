from dataclasses import dataclass

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.istasyon import Istasyon
from app.models.personel import Personel
from app.models.personel_istasyon import PersonelIstasyon
from app.models.user import User
from app.password import sifre_olustur

ROLLER = {"Admin", "Yönetici", "Satış", "Depo", "Operatör"}


@dataclass(frozen=True)
class KullaniciSonucu:
    kullanici: User | None = None
    hata: str | None = None
    durum_kodu: int = 400


def form_secenekleri(db: Session, sadece_aktif: bool = True) -> tuple[list[Istasyon], list[Personel]]:
    istasyonlar = db.query(Istasyon)
    personeller = db.query(Personel)
    if sadece_aktif:
        istasyonlar = istasyonlar.filter(Istasyon.aktif.is_(True))
        personeller = personeller.filter(Personel.aktif.is_(True))
    return istasyonlar.order_by(Istasyon.kodu).all(), personeller.order_by(Personel.ad_soyad).all()


def personel_istasyon_secenekleri(db: Session) -> dict[int, list[str]]:
    atamalar = (
        db.query(PersonelIstasyon, Istasyon)
        .join(Istasyon, Istasyon.id == PersonelIstasyon.istasyon_id)
        .filter(PersonelIstasyon.aktif.is_(True), Istasyon.aktif.is_(True))
        .order_by(Istasyon.kodu)
        .all()
    )
    sonuc = {}
    for atama, istasyon in atamalar:
        sonuc.setdefault(atama.personel_id, []).append(f"{istasyon.kodu} · {istasyon.adi}")
    return sonuc


def kullanicilari_listele(db: Session) -> list[User]:
    return db.query(User).filter(func.lower(User.kullanici_adi) != "admin").order_by(User.id.desc()).all()


def kullanici_getir(db: Session, kullanici_id: int) -> User | None:
    return db.query(User).filter(User.id == kullanici_id).first()


def _operator_baglantilari(db: Session, rol: str, personel_id: int | None, haric_id: int | None = None):
    if rol != "Operatör":
        return None, [], None
    personel = db.query(Personel).filter(Personel.id == personel_id, Personel.aktif.is_(True)).first() if personel_id else None
    istasyonlar = (
        db.query(Istasyon)
        .join(PersonelIstasyon, PersonelIstasyon.istasyon_id == Istasyon.id)
        .filter(PersonelIstasyon.personel_id == personel_id, PersonelIstasyon.aktif.is_(True), Istasyon.aktif.is_(True))
        .order_by(Istasyon.kodu)
        .all()
        if personel else []
    )
    sorgu = db.query(User).filter(User.personel_id == personel_id) if personel_id else None
    if sorgu is not None and haric_id is not None:
        sorgu = sorgu.filter(User.id != haric_id)
    return personel, istasyonlar, sorgu.first() if sorgu is not None else None


def kullanici_olustur(db: Session, **veri) -> KullaniciSonucu:
    kullanici_adi = veri["kullanici_adi"].strip()
    email = veri.get("email", "").strip() or None
    rol = veri["rol"]
    if rol not in ROLLER:
        return KullaniciSonucu(hata="Geçersiz kullanıcı rolü seçildi.")
    personel, istasyonlar, personel_kullanimda = _operator_baglantilari(db, rol, veri.get("personel_id"))
    if rol == "Operatör" and (not istasyonlar or not personel or personel_kullanimda):
        return KullaniciSonucu(hata="Operatör için en az bir yetkili istasyonu bulunan ve başka hesaba atanmamış aktif personel seçilmelidir.")
    if db.query(User).filter(User.kullanici_adi == kullanici_adi).first():
        return KullaniciSonucu(hata="Bu kullanıcı adı zaten kayıtlı.", durum_kodu=200)
    if email and db.query(User).filter(func.lower(User.email) == email.casefold()).first():
        return KullaniciSonucu(hata="Bu e-posta adresi başka bir kullanıcıda kayıtlı.")

    kullanici = User(kullanici_adi=kullanici_adi, ad_soyad=veri["ad_soyad"], telefon=veri.get("telefon", ""),
        email=email, rol=rol, istasyon_id=istasyonlar[0].id if istasyonlar else None, personel_id=personel.id if personel else None,
        aktif=veri.get("aktif", True), sifre=sifre_olustur(veri["sifre"]))
    try:
        db.add(kullanici)
        db.commit()
        return KullaniciSonucu(kullanici=kullanici)
    except IntegrityError:
        db.rollback()
        return KullaniciSonucu(hata="Kullanıcı kaydedilemedi. Kullanıcı adı veya e-posta adresi daha önce kullanılmış olabilir.")


def kullanici_guncelle(db: Session, kullanici_id: int, **veri) -> KullaniciSonucu:
    kullanici = kullanici_getir(db, kullanici_id)
    if not kullanici:
        return KullaniciSonucu()
    kullanici_adi = veri["kullanici_adi"].strip()
    email = veri.get("email", "").strip() or None
    rol = veri["rol"]
    if rol not in ROLLER:
        return KullaniciSonucu(kullanici=kullanici, hata="Geçersiz kullanıcı rolü seçildi.")
    ad_cakismasi = db.query(User).filter(func.lower(User.kullanici_adi) == kullanici_adi.casefold(), User.id != kullanici_id).first()
    email_cakismasi = db.query(User).filter(func.lower(User.email) == email.casefold(), User.id != kullanici_id).first() if email else None
    if ad_cakismasi or email_cakismasi:
        return KullaniciSonucu(kullanici=kullanici, hata="Bu kullanıcı adı başka bir kullanıcıda kayıtlı." if ad_cakismasi else "Bu e-posta adresi başka bir kullanıcıda kayıtlı.")
    personel, istasyonlar, personel_kullanimda = _operator_baglantilari(db, rol, veri.get("personel_id"), kullanici_id)
    if rol == "Operatör" and (not istasyonlar or not personel or personel_kullanimda):
        return KullaniciSonucu(kullanici=kullanici, hata="Operatör için en az bir yetkili istasyonu bulunan ve başka hesaba atanmamış aktif personel seçilmelidir.")
    kullanici.kullanici_adi, kullanici.ad_soyad, kullanici.telefon = kullanici_adi, veri.get("ad_soyad", ""), veri.get("telefon", "")
    kullanici.email, kullanici.rol, kullanici.aktif = email, rol, veri.get("aktif", True)
    kullanici.istasyon_id, kullanici.personel_id = (istasyonlar[0].id, personel.id) if rol == "Operatör" else (None, None)
    if veri.get("sifre", "").strip():
        kullanici.sifre = sifre_olustur(veri["sifre"])
    try:
        db.commit()
        return KullaniciSonucu(kullanici=kullanici)
    except IntegrityError:
        db.rollback()
        return KullaniciSonucu(kullanici=kullanici, hata="Kullanıcı kaydedilemedi. Kullanıcı adı veya e-posta adresi daha önce kullanılmış olabilir.")


def kullanici_sil(db: Session, kullanici_id: int) -> None:
    kullanici = kullanici_getir(db, kullanici_id)
    if kullanici:
        db.delete(kullanici)
        db.commit()
