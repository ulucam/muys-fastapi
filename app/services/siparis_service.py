from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.musteri import Musteri
from app.models.siparis import Siparis
from app.models.siparis_kalem import SiparisKalem
from app.models.urun import Urun

SIPARIS_DURUMLARI = ("Beklemede", "Üretimde", "Sevke Hazır")


@dataclass(frozen=True)
class SiparisHatasi(Exception):
    durum_kodu: int
    mesaj: str


def siparisleri_listele(db: Session):
    siparisler = db.query(Siparis).order_by(Siparis.created_at.desc()).all()
    return [{
        "id": s.id, "siparis_no": s.siparis_no, "musteri_id": s.musteri_id,
        "musteri_adi": s.musteri.firma_adi if s.musteri else "-", "siparis_tarihi": s.siparis_tarihi,
        "teslim_tarihi": s.teslim_tarihi, "durum": s.durum, "notlar": s.notlar,
        "toplam_tutar": sum(k.miktar * (k.birim_fiyat or 0) for k in s.kalemler),
    } for s in siparisler]


def siparis_sayfasi_verisi(db: Session, musteri_id: int | None, durum: str | None):
    musteri = db.query(Musteri).filter(Musteri.id == musteri_id).first() if musteri_id else None
    sorgu = db.query(Siparis)
    if musteri_id:
        sorgu = sorgu.filter(Siparis.musteri_id == musteri_id)
    if durum:
        sorgu = sorgu.filter(Siparis.durum == durum)
    siparisler = sorgu.order_by(Siparis.teslim_tarihi.asc(), Siparis.created_at.desc()).all()
    return musteri, {d: [s for s in siparisler if s.durum == d] for d in SIPARIS_DURUMLARI}


def siparis_olustur(db: Session, siparis_data):
    if db.query(Siparis).filter(Siparis.siparis_no == siparis_data.siparis_no).first():
        raise SiparisHatasi(400, "Bu sipariş no zaten kullanılıyor!")
    musteri = db.query(Musteri).filter(Musteri.id == siparis_data.musteri_id).first()
    if not musteri:
        raise SiparisHatasi(404, "Müşteri bulunamadı!")
    siparis = Siparis(siparis_no=siparis_data.siparis_no, musteri_id=siparis_data.musteri_id,
        teslim_tarihi=siparis_data.teslim_tarihi, notlar=siparis_data.notlar, durum="Beklemede")
    db.add(siparis)
    db.flush()
    toplam = 0
    for kalem_data in siparis_data.kalemler:
        urun = db.query(Urun).filter(Urun.id == kalem_data.urun_id).first()
        if not urun:
            db.rollback()
            raise SiparisHatasi(404, f"Ürün ID {kalem_data.urun_id} bulunamadı!")
        birim_fiyat = kalem_data.birim_fiyat or urun.birim_fiyat or 0
        satir_toplam = kalem_data.miktar * birim_fiyat
        toplam += satir_toplam
        db.add(SiparisKalem(siparis_id=siparis.id, urun_id=kalem_data.urun_id, miktar=kalem_data.miktar,
            birim_fiyat=birim_fiyat, toplam_tutar=satir_toplam))
    db.commit()
    db.refresh(siparis)
    return {"id": siparis.id, "siparis_no": siparis.siparis_no, "musteri_id": siparis.musteri_id,
        "musteri_adi": musteri.firma_adi, "siparis_tarihi": siparis.siparis_tarihi,
        "teslim_tarihi": siparis.teslim_tarihi, "durum": siparis.durum,
        "notlar": siparis.notlar, "toplam_tutar": toplam}
