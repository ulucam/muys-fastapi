from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.recete import Recete
from app.models.urun import Urun
from app.models.stok_urun_sinifi import StokUrunSinifi
from app.models.stok_urun_turu import StokUrunTuru


def stok_urunlerini_listele(db: Session):
    return db.query(Urun).order_by(Urun.adi).all()


def hammaddeleri_listele(db: Session):
    return (
        db.query(Urun)
        .join(StokUrunTuru, StokUrunTuru.id == Urun.stok_urun_turu_id)
        .filter(StokUrunTuru.uretilen.is_(False))
        .order_by(Urun.kodu)
        .all()
    )


def hammaddeleri_filtrele(db: Session, arama: str = "", urun_id: int | None = None, tur_id: int | None = None, sinif_id: int | None = None):
    """Reçeteler ekranındaki stok kartlarını kayıtlı tür/sınıf değerleriyle süzer."""
    sorgu = (
        db.query(Urun)
        .join(StokUrunTuru, StokUrunTuru.id == Urun.stok_urun_turu_id)
        .filter(StokUrunTuru.uretilen.is_(False))
    )
    if arama.strip():
        desen = f"%{arama.strip()}%"
        sorgu = sorgu.filter((Urun.kodu.ilike(desen)) | (Urun.adi.ilike(desen)))
    if urun_id:
        sorgu = sorgu.filter(Urun.id == urun_id)
    if tur_id:
        sorgu = sorgu.filter(Urun.stok_urun_turu_id == tur_id)
    if sinif_id:
        sorgu = sorgu.filter(Urun.stok_urun_sinifi_id == sinif_id)
    return sorgu.order_by(Urun.kodu).all()


def stok_tanimlari(db: Session):
    return (
        db.query(StokUrunTuru).filter(StokUrunTuru.aktif.is_(True)).order_by(StokUrunTuru.adi).all(),
        db.query(StokUrunSinifi).filter(StokUrunSinifi.aktif.is_(True)).order_by(StokUrunSinifi.adi).all(),
    )


def stok_tum_tanimlari(db: Session):
    return (
        db.query(StokUrunTuru).filter(StokUrunTuru.aktif.is_(True)).order_by(StokUrunTuru.adi).all(),
        db.query(StokUrunSinifi).filter(StokUrunSinifi.aktif.is_(True)).order_by(StokUrunSinifi.adi).all(),
    )


def stok_tanim_kullanimlari(db: Session) -> dict[str, dict[int, int]]:
    turler = dict(db.query(Urun.stok_urun_turu_id, func.count(Urun.id)).filter(Urun.stok_urun_turu_id.isnot(None)).group_by(Urun.stok_urun_turu_id).all())
    siniflar = dict(db.query(Urun.stok_urun_sinifi_id, func.count(Urun.id)).filter(Urun.stok_urun_sinifi_id.isnot(None)).group_by(Urun.stok_urun_sinifi_id).all())
    return {"turler": turler, "siniflar": siniflar}


def stok_kurulum_durumu(db: Session) -> dict:
    tur_sayisi = db.query(StokUrunTuru).filter(StokUrunTuru.aktif.is_(True), StokUrunTuru.uretilen.is_(False)).count()
    sinif_sayisi = db.query(StokUrunSinifi).filter(StokUrunSinifi.aktif.is_(True)).count()
    hammadde_sayisi = (
        db.query(Urun)
        .join(StokUrunTuru, StokUrunTuru.id == Urun.stok_urun_turu_id)
        .filter(Urun.aktif.is_(True), StokUrunTuru.uretilen.is_(False))
        .count()
    )
    return {
        "turler_hazir": tur_sayisi > 0,
        "siniflar_hazir": sinif_sayisi > 0,
        "hammadde_hazir": hammadde_sayisi > 0,
        "hammadde_eklenebilir": tur_sayisi > 0 and sinif_sayisi > 0,
        "yari_mamul_eklenebilir": hammadde_sayisi > 0,
    }


def stok_urunu_kaydet(
    db: Session, kodu: str, adi: str, tur_id: int, sinif_id: int | None,
    birim: str, marka: str = "", model: str = "", mevcut_stok: float = 0,
    min_stok: float = 0, urun_id: int | None = None,
):
    if birim.strip() not in {"Adet", "Kg"}:
        raise ValueError("Birim Adet veya Kg olmalıdır")
    tur = db.query(StokUrunTuru).filter(StokUrunTuru.id == tur_id, StokUrunTuru.aktif.is_(True)).first()
    sinif = db.query(StokUrunSinifi).filter(StokUrunSinifi.id == sinif_id, StokUrunSinifi.aktif.is_(True)).first() if sinif_id else None
    if db.query(StokUrunSinifi).filter(StokUrunSinifi.aktif.is_(True)).count() == 0:
        raise ValueError("Hammadde kartından önce en az bir takip sınıfı tanımlanmalıdır")
    if not adi.strip() or not tur or (sinif_id and not sinif):
        raise ValueError("Ürün adı ve geçerli tür zorunludur")
    urun = db.query(Urun).filter(Urun.id == urun_id).first() if urun_id else None
    if not kodu.strip() and not urun:
        kullanilan = {kod for (kod,) in db.query(Urun.kodu).all() if kod}
        sira = 1
        kodu = f"STK-{sira:04d}"
        while kodu in kullanilan:
            sira += 1
            kodu = f"STK-{sira:04d}"
    kod_cakismasi = db.query(Urun).filter(Urun.kodu == kodu.strip(), Urun.id != (urun.id if urun else 0)).first()
    if kod_cakismasi:
        raise ValueError("Bu stok kodu başka bir üründe kullanılıyor")
    urun = urun or Urun(kodu=kodu.strip())
    urun.kodu = kodu.strip()
    urun.adi, urun.stok_urun_turu_id, urun.stok_urun_sinifi_id = adi.strip(), tur.id, sinif.id if sinif else None
    urun_tipi = "YariMamul" if tur.uretilen else ("TicariMamul" if "ticari" in tur.adi.casefold() else "Hammadde")
    urun.urun_tipi, urun.birim, urun.aktif = urun_tipi, birim.strip(), True
    urun.marka, urun.model = marka.strip(), model.strip()
    urun.mevcut_stok, urun.min_stok = mevcut_stok, min_stok
    db.add(urun); db.commit()
    return urun


def stok_urunlerini_toplu_guncelle(db: Session, form) -> int:
    """Yalnızca kullanıcı tarafından açılmış stok kartlarını tek işlemde günceller."""
    try:
        urun_idleri = {int(urun_id) for urun_id in form.getlist("urun_idleri")}
        if not urun_idleri:
            raise ValueError("Güncellenecek açık kart bulunamadı")
        guncellenen = 0
        for urun_id in urun_idleri:
            onek = f"urun_{urun_id}_"
            urun = db.query(Urun).filter(Urun.id == urun_id).first()
            tur_id = int(form.get(f"{onek}tur_id") or 0)
            sinif_degeri = form.get(f"{onek}sinif_id")
            sinif_id = int(sinif_degeri) if sinif_degeri else None
            tur = db.query(StokUrunTuru).filter(
                StokUrunTuru.id == tur_id, StokUrunTuru.aktif.is_(True), StokUrunTuru.uretilen.is_(False)
            ).first()
            sinif = db.query(StokUrunSinifi).filter(StokUrunSinifi.id == sinif_id, StokUrunSinifi.aktif.is_(True)).first() if sinif_id else None
            kodu, adi = str(form.get(f"{onek}kodu") or "").strip(), str(form.get(f"{onek}adi") or "").strip()
            if not urun or not kodu or not adi or not tur or (sinif_id and not sinif):
                raise ValueError("Açık kartlardaki zorunlu alanları kontrol edin")
            cakisan = db.query(Urun).filter(Urun.kodu == kodu, Urun.id != urun.id).first()
            if cakisan:
                raise ValueError(f"{kodu} stok kodu başka bir üründe kullanılıyor")
            birim = str(form.get(f"{onek}birim") or "").strip()
            if birim not in {"Adet", "Kg"}:
                raise ValueError("Birim Adet veya Kg olmalıdır")
            urun.kodu, urun.adi = kodu, adi
            urun.stok_urun_turu_id, urun.stok_urun_sinifi_id = tur.id, sinif.id if sinif else None
            urun.marka, urun.model, urun.birim = str(form.get(f"{onek}marka") or "").strip(), str(form.get(f"{onek}model") or "").strip(), birim
            urun.mevcut_stok = float(form.get(f"{onek}mevcut_stok") or 0)
            urun.min_stok = float(form.get(f"{onek}min_stok") or 0)
            guncellenen += 1
        db.commit()
        return guncellenen
    except (TypeError, ValueError):
        db.rollback()
        raise ValueError("Kart değerlerini ve sayısal alanları kontrol edin")
    except Exception:
        db.rollback()
        raise


def stok_turu_kaydet(db: Session, adi: str, tur_id: int | None = None):
    temiz_ad = adi.strip()
    tur = db.query(StokUrunTuru).filter(StokUrunTuru.id == tur_id, StokUrunTuru.uretilen.is_(False)).first() if tur_id else None
    if tur_id and not tur:
        raise ValueError("Güncellenecek tür bulunamadı")
    cakisan = next((kayit for kayit in db.query(StokUrunTuru).all() if kayit.id != (tur.id if tur else 0) and kayit.adi.casefold() == temiz_ad.casefold()), None)
    if not temiz_ad or (cakisan and (tur is not None or cakisan.aktif)):
        raise ValueError("Tür adı zorunludur ve benzersiz olmalıdır")
    tur = tur or cakisan or StokUrunTuru(uretilen=False)
    tur.adi, tur.aktif = temiz_ad, True
    db.add(tur); db.commit()
    return tur


def stok_sinifi_kaydet(db: Session, adi: str, sinif_id: int | None = None):
    temiz_ad = adi.strip()
    sinif = db.query(StokUrunSinifi).filter(StokUrunSinifi.id == sinif_id).first() if sinif_id else None
    if sinif_id and not sinif:
        raise ValueError("Güncellenecek sınıf bulunamadı")
    cakisan = next((kayit for kayit in db.query(StokUrunSinifi).all() if kayit.id != (sinif.id if sinif else 0) and kayit.adi.casefold() == temiz_ad.casefold()), None)
    if not temiz_ad or (cakisan and (sinif is not None or cakisan.aktif)):
        raise ValueError("Sınıf adı zorunludur ve benzersiz olmalıdır")
    sinif = sinif or cakisan or StokUrunSinifi()
    sinif.adi, sinif.aktif = temiz_ad, True
    db.add(sinif); db.commit()
    return sinif


def stok_turu_sil(db: Session, tur_id: int, urunlerden_kaldir: bool = False) -> int:
    tur = db.query(StokUrunTuru).filter(StokUrunTuru.id == tur_id, StokUrunTuru.uretilen.is_(False)).first()
    if not tur:
        raise ValueError("Silinecek tür bulunamadı")
    urunler = db.query(Urun).filter(Urun.stok_urun_turu_id == tur.id).all()
    if urunler and not urunlerden_kaldir:
        raise ValueError("Tür ürünlerde kullanılıyor")
    for urun in urunler:
        urun.stok_urun_turu_id = None
    tur.aktif = False
    db.commit()
    return len(urunler)


def stok_sinifi_sil(db: Session, sinif_id: int, urunlerden_kaldir: bool = False) -> int:
    sinif = db.query(StokUrunSinifi).filter(StokUrunSinifi.id == sinif_id).first()
    if not sinif:
        raise ValueError("Silinecek sınıf bulunamadı")
    urunler = db.query(Urun).filter(Urun.stok_urun_sinifi_id == sinif.id).all()
    if urunler and not urunlerden_kaldir:
        raise ValueError("Sınıf ürünlerde kullanılıyor")
    for urun in urunler:
        urun.stok_urun_sinifi_id = None
    sinif.aktif = False
    db.commit()
    return len(urunler)


def receteleri_listele(db: Session):
    return db.query(Recete).order_by(Recete.id.desc()).all()
