from dataclasses import dataclass
from datetime import datetime

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


def siparis_form_verisi(db: Session, siparis_id: int | None = None) -> dict:
    siparis = db.query(Siparis).filter(Siparis.id == siparis_id).first() if siparis_id else None
    return {
        "siparis": siparis,
        "kalemler": db.query(SiparisKalem).filter(SiparisKalem.siparis_id == siparis.id, SiparisKalem.aktif.is_(True)).order_by(SiparisKalem.sira_no).all() if siparis else [],
        "musteriler": db.query(Musteri).filter(Musteri.aktif.is_(True)).order_by(Musteri.firma_adi).all(),
        "urunler": db.query(Urun).filter(Urun.aktif.is_(True)).order_by(Urun.adi).all(),
    }


def _siparis_no_uret(db: Session) -> str:
    numaralar = [int(no[3:]) for (no,) in db.query(Siparis.siparis_no).all() if no and no.startswith("SIP") and no[3:].isdigit()]
    return f"SIP{max(numaralar, default=0) + 1:06d}"


def siparis_formunu_kaydet(db: Session, siparis_id: int | None, form) -> Siparis:
    """Sipariş başlığı ve kalemlerini web formundan güvenli biçimde kaydeder."""
    try:
        musteri_id = int(form.get("musteri_id") or 0)
        musteri = db.query(Musteri).filter(Musteri.id == musteri_id, Musteri.aktif.is_(True)).first()
        if not musteri:
            raise ValueError("Geçerli müşteri seçin")
        siparis = db.query(Siparis).filter(Siparis.id == siparis_id, Siparis.aktif.is_(True)).first() if siparis_id else None
        if siparis_id and not siparis:
            raise ValueError("Düzenlenecek sipariş bulunamadı")
        siparis_no = (form.get("siparis_no") or "").strip() or _siparis_no_uret(db)
        cakisan = db.query(Siparis).filter(Siparis.siparis_no == siparis_no, Siparis.id != (siparis.id if siparis else 0)).first()
        if cakisan:
            raise ValueError("Bu sipariş numarası kullanılıyor")
        teslim = (form.get("teslim_tarihi") or "").strip()
        teslim_tarihi = datetime.strptime(teslim, "%Y-%m-%d") if teslim else None
        siparis = siparis or Siparis(siparis_no=siparis_no, durum="Beklemede", aktif=True)
        siparis.siparis_no, siparis.musteri_id = siparis_no, musteri.id
        siparis.teslim_tarihi, siparis.aciklama = teslim_tarihi, (form.get("aciklama") or "").strip()[:500]
        durum = form.get("durum") or "Beklemede"
        if durum not in SIPARIS_DURUMLARI:
            raise ValueError("Geçerli sipariş durumu seçin")
        siparis.durum = durum
        db.add(siparis); db.flush()

        kalem_idleri = form.getlist("kalem_id")
        urun_idleri, miktarlar = form.getlist("urun_id"), form.getlist("miktar")
        if not urun_idleri:
            raise ValueError("En az bir ürün kalemi ekleyin")
        mevcutlar = {kalem.id: kalem for kalem in db.query(SiparisKalem).filter(SiparisKalem.siparis_id == siparis.id).all()}
        secili_kalemler = set()
        for sira, (kalem_id, urun_id, miktar) in enumerate(zip(kalem_idleri, urun_idleri, miktarlar), start=1):
            urun = db.query(Urun).filter(Urun.id == int(urun_id or 0), Urun.aktif.is_(True)).first()
            adet = int(miktar or 0)
            if not urun or adet < 1:
                raise ValueError("Her kalemde ürün ve pozitif tam sayı miktar zorunlu")
            kalem = mevcutlar.get(int(kalem_id)) if str(kalem_id).isdigit() else None
            kalem = kalem or SiparisKalem(siparis_id=siparis.id)
            kalem.urun_id, kalem.miktar, kalem.birim, kalem.sira_no, kalem.aktif = urun.id, adet, urun.birim or "Adet", sira, True
            db.add(kalem); db.flush(); secili_kalemler.add(kalem.id)
        for kalem_id, kalem in mevcutlar.items():
            if kalem_id not in secili_kalemler:
                kalem.aktif = False
        db.commit()
        return siparis
    except Exception:
        db.rollback()
        raise


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
