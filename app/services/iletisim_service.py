from datetime import datetime

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.bildirim import Bildirim
from app.models.mesaj import Mesaj
from app.models.mesaj_konusu import MesajAlici, MesajKonusu, MesajKonusuYetkili, MesajSilme
from app.models.user import User


def aktif_kullanicilar(db: Session, haric_id: int):
    return db.query(User).filter(User.aktif.is_(True), User.id != haric_id).order_by(User.ad_soyad).all()


def bildirim_olustur(db: Session, kullanici_id: int, baslik: str, mesaj: str, tur: str = "bilgi", baglanti: str = ""):
    bildirim = Bildirim(kullanici_id=kullanici_id, baslik=baslik[:120], mesaj=mesaj[:500], tur=tur[:30], baglanti=baglanti[:300])
    db.add(bildirim)
    return bildirim


def mesaj_konulari_verisi(db: Session) -> dict:
    konular = db.query(MesajKonusu).filter(MesajKonusu.aktif.is_(True)).order_by(MesajKonusu.adi).all()
    yetkililer = {}
    for kayit in db.query(MesajKonusuYetkili).all():
        yetkililer.setdefault(kayit.konu_id, set()).add(kayit.kullanici_id)
    return {"mesaj_konulari": konular, "mesaj_konu_haritasi": {konu.id: konu for konu in konular}, "konu_yetkilileri": yetkililer}


def mesaj_konusu_kaydet(db: Session, konu_id: int | None, adi: str, renk: str, kullanici_idleri) -> MesajKonusu:
    adi = adi.strip()
    if not adi or len(adi) > 80:
        raise ValueError("Konu adı geçersiz")
    konu = db.query(MesajKonusu).filter(MesajKonusu.id == konu_id).first() if konu_id else MesajKonusu()
    if konu_id and not konu:
        raise ValueError("Konu bulunamadı")
    cakisan = db.query(MesajKonusu).filter(MesajKonusu.adi == adi, MesajKonusu.id != (konu.id or 0)).first()
    if cakisan:
        raise ValueError("Konu adı kullanılıyor")
    konu.adi, konu.renk, konu.aktif = adi, renk if renk in {"primary", "info", "warning", "success", "danger", "dark"} else "primary", True
    db.add(konu); db.flush()
    secilenler = {int(x) for x in kullanici_idleri if str(x).isdigit()}
    db.query(MesajKonusuYetkili).filter(MesajKonusuYetkili.konu_id == konu.id).delete(synchronize_session=False)
    for kullanici_id in secilenler:
        db.add(MesajKonusuYetkili(konu_id=konu.id, kullanici_id=kullanici_id))
    db.commit()
    return konu


def _alici_kayitlarini_ekle(db: Session, mesaj: Mesaj, kullanici_idleri: set[int]) -> None:
    for kullanici_id in kullanici_idleri - {mesaj.gonderen_id}:
        db.add(MesajAlici(mesaj_id=mesaj.id, kullanici_id=kullanici_id))


def mesaj_gonder(db: Session, gonderen_id: int, alici_id: int, konu_id: int, baslik: str, icerik: str):
    baslik, icerik = baslik.strip(), icerik.strip()
    alici = db.query(User).filter(User.id == alici_id, User.aktif.is_(True)).first()
    gonderen = db.query(User).filter(User.id == gonderen_id, User.aktif.is_(True)).first()
    mesaj_konusu = db.query(MesajKonusu).filter(MesajKonusu.id == konu_id, MesajKonusu.aktif.is_(True)).first()
    if not alici or not gonderen or alici.id == gonderen.id:
        raise ValueError("Geçerli bir alıcı seçin")
    if not mesaj_konusu or not baslik or not icerik or len(baslik) > 150 or len(icerik) > 5000:
        raise ValueError("Konu ve mesaj zorunludur; mesaj en fazla 5000 karakter olabilir")
    mesaj = Mesaj(gonderen_id=gonderen.id, alici_id=alici.id, konu_id=mesaj_konusu.id, konu=baslik, icerik=icerik)
    db.add(mesaj)
    db.flush()
    mesaj.konusma_id = mesaj.id
    yetkili_idleri = {x.kullanici_id for x in db.query(MesajKonusuYetkili).filter(MesajKonusuYetkili.konu_id == mesaj_konusu.id).all()}
    alici_idleri = yetkili_idleri | {alici.id}
    _alici_kayitlarini_ekle(db, mesaj, alici_idleri)
    for hedef_id in alici_idleri - {gonderen.id}:
        bildirim_olustur(db, hedef_id, f"{mesaj_konusu.adi}: Yeni mesaj", f"{gonderen.ad_soyad}: {baslik}", "mesaj", f"/mesajlar#konusma-{mesaj.id}")
    db.commit()
    return mesaj, alici_idleri - {gonderen.id}, mesaj_konusu


def mesaji_yanitla(db: Session, kullanici_id: int, mesaj_id: int, icerik: str):
    icerik = icerik.strip()
    onceki = db.query(Mesaj).filter(Mesaj.id == mesaj_id).first()
    yetkili_alici = onceki and db.query(MesajAlici).filter(MesajAlici.mesaj_id == onceki.id, MesajAlici.kullanici_id == kullanici_id).first()
    if not onceki or (onceki.gonderen_id != kullanici_id and onceki.alici_id != kullanici_id and not yetkili_alici) or not icerik or len(icerik) > 5000:
        raise ValueError("Cevap metni geçersiz")
    alici_id = onceki.alici_id if onceki.gonderen_id == kullanici_id else onceki.gonderen_id
    gonderen = db.query(User).filter(User.id == kullanici_id, User.aktif.is_(True)).first()
    alici = db.query(User).filter(User.id == alici_id, User.aktif.is_(True)).first()
    if not gonderen or not alici:
        raise ValueError("Kullanıcı bulunamadı")
    konusma_id = onceki.konusma_id or onceki.id
    konu = onceki.konu if onceki.konu.lower().startswith("re:") else f"Re: {onceki.konu}"
    cevap = Mesaj(gonderen_id=kullanici_id, alici_id=alici_id, konusma_id=konusma_id, konu_id=onceki.konu_id, konu=konu[:150], icerik=icerik)
    db.add(cevap)
    db.flush()
    konusma_mesajlari = db.query(Mesaj).filter(Mesaj.konusma_id == konusma_id).all()
    katilimcilar = {m.gonderen_id for m in konusma_mesajlari} | {m.alici_id for m in konusma_mesajlari}
    katilimcilar |= {x.kullanici_id for x in db.query(MesajKonusuYetkili).filter(MesajKonusuYetkili.konu_id == onceki.konu_id).all()}
    _alici_kayitlarini_ekle(db, cevap, katilimcilar)
    for hedef_id in katilimcilar - {kullanici_id}:
        bildirim_olustur(db, hedef_id, "Mesajınıza cevap", f"{gonderen.ad_soyad} mesajınıza cevap verdi", "mesaj", f"/mesajlar#konusma-{konusma_id}")
    db.commit()
    return cevap, katilimcilar - {kullanici_id}, konusma_id


def mesaj_kutulari(db: Session, kullanici_id: int) -> dict:
    kullanicilar = {k.id: k for k in db.query(User).all()}
    gelen = db.query(Mesaj).filter(Mesaj.alici_id == kullanici_id, Mesaj.alici_sildi.is_(False)).order_by(Mesaj.created_at.desc()).limit(200).all()
    teslim_mesaj_idleri = {x.mesaj_id for x in db.query(MesajAlici).filter(MesajAlici.kullanici_id == kullanici_id).all()}
    tumu = db.query(Mesaj).filter(or_(Mesaj.gonderen_id == kullanici_id, Mesaj.alici_id == kullanici_id, Mesaj.id.in_(teslim_mesaj_idleri or {-1}))).order_by(Mesaj.created_at).limit(500).all()
    gruplar = {}
    silinen_konusmalar = {x.konusma_id for x in db.query(MesajSilme).filter(MesajSilme.kullanici_id == kullanici_id).all()}
    for mesaj in tumu:
        konusma_id = mesaj.konusma_id or mesaj.id
        if konusma_id not in silinen_konusmalar:
            gruplar.setdefault(konusma_id, []).append(mesaj)
    konusmalar = [{
        "id": konusma_id, "mesajlar": mesajlar, "ilk": mesajlar[0], "son": mesajlar[-1],
        "okunmamis": db.query(MesajAlici).filter(MesajAlici.kullanici_id == kullanici_id, MesajAlici.mesaj_id.in_([m.id for m in mesajlar]), MesajAlici.okundu.is_(False)).count(),
    } for konusma_id, mesajlar in gruplar.items()]
    konusmalar.sort(key=lambda kayit: kayit["son"].created_at, reverse=True)
    okunmamis = db.query(MesajAlici).filter(MesajAlici.kullanici_id == kullanici_id, MesajAlici.okundu.is_(False)).count()
    return {"gelen": gelen, "konusmalar": konusmalar, "kullanicilar": kullanicilar, "okunmamis": okunmamis}


def konusmayi_sil(db: Session, konusma_id: int, kullanici_id: int) -> str:
    mesajlar = db.query(Mesaj).filter(Mesaj.konusma_id == konusma_id).order_by(Mesaj.created_at).all()
    erisim = any(m.gonderen_id == kullanici_id or m.alici_id == kullanici_id for m in mesajlar)
    if not erisim:
        mesaj_idleri = [m.id for m in mesajlar]
        erisim = bool(mesaj_idleri and db.query(MesajAlici).filter(MesajAlici.kullanici_id == kullanici_id, MesajAlici.mesaj_id.in_(mesaj_idleri)).first())
    if not mesajlar or not erisim:
        raise ValueError("Konuşma bulunamadı")
    kayit = db.query(MesajSilme).filter(MesajSilme.konusma_id == konusma_id, MesajSilme.kullanici_id == kullanici_id).first()
    if not kayit:
        db.add(MesajSilme(konusma_id=konusma_id, kullanici_id=kullanici_id))
    simdi = datetime.utcnow()
    for alici in db.query(MesajAlici).filter(MesajAlici.kullanici_id == kullanici_id, MesajAlici.mesaj_id.in_([m.id for m in mesajlar])).all():
        alici.okundu, alici.okunma_tarihi = True, simdi
    db.flush()
    icerik_ozeti = " | ".join(f"#{m.id} {m.konu}: {m.icerik}" for m in mesajlar)
    return f"Konuşma #{konusma_id}, {len(mesajlar)} mesaj. {icerik_ozeti[:4000]}"


def mesaji_okundu_yap(db: Session, mesaj_id: int, kullanici_id: int) -> int | None:
    mesaj = db.query(Mesaj).filter(Mesaj.id == mesaj_id).first()
    yetkili_alici = mesaj and db.query(MesajAlici).filter(MesajAlici.mesaj_id == mesaj.id, MesajAlici.kullanici_id == kullanici_id).first()
    if not mesaj or (mesaj.gonderen_id != kullanici_id and mesaj.alici_id != kullanici_id and not yetkili_alici):
        return None
    konusma_id = mesaj.konusma_id or mesaj.id
    okunmamislar = db.query(Mesaj).filter(Mesaj.konusma_id == konusma_id, Mesaj.alici_id == kullanici_id, Mesaj.okundu.is_(False)).all()
    alici_kayitlari = db.query(MesajAlici).filter(MesajAlici.kullanici_id == kullanici_id, MesajAlici.mesaj_id.in_([m.id for m in db.query(Mesaj).filter(Mesaj.konusma_id == konusma_id).all()]), MesajAlici.okundu.is_(False)).all()
    bildirimler = db.query(Bildirim).filter(Bildirim.kullanici_id == kullanici_id, Bildirim.baglanti == f"/mesajlar#konusma-{konusma_id}", Bildirim.okundu.is_(False)).all()
    if okunmamislar or alici_kayitlari or bildirimler:
        simdi = datetime.utcnow()
        for kayit in okunmamislar:
            kayit.okundu, kayit.okunma_tarihi = True, simdi
        for kayit in alici_kayitlari:
            kayit.okundu, kayit.okunma_tarihi = True, simdi
        for bildirim in bildirimler:
            bildirim.okundu, bildirim.okunma_tarihi = True, simdi
        db.commit()
    return konusma_id


def bildirimleri_okundu_yap(db: Session, kullanici_id: int) -> int:
    bildirimler = db.query(Bildirim).filter(Bildirim.kullanici_id == kullanici_id, Bildirim.okundu.is_(False)).all()
    simdi = datetime.utcnow()
    for bildirim in bildirimler:
        bildirim.okundu, bildirim.okunma_tarihi = True, simdi
    db.commit()
    return len(bildirimler)


def bildirimi_okundu_yap(db: Session, bildirim_id: int, kullanici_id: int) -> bool:
    bildirim = db.query(Bildirim).filter(Bildirim.id == bildirim_id, Bildirim.kullanici_id == kullanici_id).first()
    if not bildirim:
        return False
    if not bildirim.okundu:
        bildirim.okundu, bildirim.okunma_tarihi = True, datetime.utcnow()
        db.commit()
    return True


def iletisim_ozeti(db: Session, kullanici_id: int) -> dict:
    bildirimler = db.query(Bildirim).filter(Bildirim.kullanici_id == kullanici_id).order_by(Bildirim.created_at.desc()).limit(8).all()
    okunmamis_bildirim = db.query(Bildirim).filter(Bildirim.kullanici_id == kullanici_id, Bildirim.okundu.is_(False)).count()
    okunmamis_mesaj = db.query(MesajAlici).filter(MesajAlici.kullanici_id == kullanici_id, MesajAlici.okundu.is_(False)).count()
    return {
        "okunmamis_bildirim": okunmamis_bildirim,
        "okunmamis_mesaj": okunmamis_mesaj,
        "bildirimler": [{
            "id": b.id, "baslik": b.baslik, "mesaj": b.mesaj, "tur": b.tur, "baglanti": b.baglanti,
            "okundu": b.okundu, "zaman": b.created_at.strftime("%d.%m.%Y %H:%M"),
        } for b in bildirimler],
    }
