import io

import openpyxl
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.musteri import Musteri
from app.models.siparis import Siparis


def musterileri_listele(db: Session) -> tuple[list[Musteri], list[Musteri]]:
    aktifler = db.query(Musteri).filter(Musteri.aktif.is_(True)).order_by(Musteri.firma_adi.asc()).all()
    pasifler = db.query(Musteri).filter(Musteri.aktif.is_(False)).order_by(Musteri.firma_adi.asc()).all()
    return aktifler, pasifler


def musteri_getir(db: Session, musteri_id: int) -> Musteri | None:
    return db.query(Musteri).filter(Musteri.id == musteri_id).first()


def _sonraki_musteri_kodu(db: Session) -> str:
    son = db.query(Musteri).order_by(Musteri.id.desc()).first()
    return f"M{son.id + 1:06}" if son else "M000001"


def musteri_olustur(db: Session, **alanlar) -> Musteri:
    musteri = Musteri(musteri_kodu=_sonraki_musteri_kodu(db), **alanlar)
    db.add(musteri)
    db.commit()
    return musteri


def musteri_guncelle(db: Session, musteri_id: int, **alanlar) -> Musteri | None:
    musteri = musteri_getir(db, musteri_id)
    if not musteri:
        return None
    for alan, deger in alanlar.items():
        setattr(musteri, alan, deger)
    db.commit()
    return musteri


def musteri_detayi(db: Session, musteri_id: int) -> tuple[Musteri | None, dict[str, int]]:
    musteri = musteri_getir(db, musteri_id)
    if not musteri:
        return None, {}
    siparisler = db.query(Siparis).filter(Siparis.musteri_id == musteri.id).all()
    return musteri, {
        "bekleyen_siparis": sum(s.durum == "Beklemede" for s in siparisler),
        "uretimdeki_siparis": sum(s.durum == "Üretimde" for s in siparisler),
        "tamamlanan_siparis": sum(s.durum == "Tamamlandı" for s in siparisler),
        "toplam_siparis": len(siparisler),
    }


def musteri_sil(db: Session, musteri_id: int) -> bool:
    musteri = musteri_getir(db, musteri_id)
    if not musteri:
        return True
    try:
        db.delete(musteri)
        db.commit()
        return True
    except IntegrityError:
        db.rollback()
        return False


def musterileri_excelden_aktar(db: Session, dosya_icerigi: bytes) -> None:
    try:
        kitap = openpyxl.load_workbook(filename=io.BytesIO(dosya_icerigi), data_only=True)
        sayfa = kitap.active
        basliklar = [str(hucre.value or "").strip().lower().replace(" ", "_") for hucre in sayfa[1]]

        for satir in sayfa.iter_rows(min_row=2, values_only=True):
            if not any(satir):
                continue
            veri = dict(zip(basliklar, satir))
            firma_adi = str(veri.get("firma_adi") or veri.get("firma_adı") or "").strip()
            if not firma_adi or firma_adi.lower() == "none":
                continue

            def temizle(alan: str) -> str:
                deger = veri.get(alan)
                return "" if deger is None or str(deger).lower() == "none" else str(deger).strip()

            db.add(Musteri(
                musteri_kodu=_sonraki_musteri_kodu(db), firma_adi=firma_adi,
                yetkili=temizle("yetkili"), telefon=temizle("telefon"), email=temizle("email"),
                vergi_dairesi=temizle("vergi_dairesi"), vergi_no=temizle("vergi_no"),
                il=temizle("il"), ilce=temizle("ilce"), adres=temizle("adres"),
                aciklama=temizle("aciklama"), aktif=True,
            ))
            db.flush()
        db.commit()
    except Exception:
        db.rollback()
        raise
