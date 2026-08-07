import json
import secrets
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.excel_aktarim_taslagi import ExcelAktarimTaslagi
from app.models.istasyon import Istasyon
from app.models.makine import Makine
from app.models.musteri import Musteri
from app.models.personel import Personel
from app.models.personel_istasyon import PersonelIstasyon
from app.models.urun import Urun
from app.models.stok_urun_turu import StokUrunTuru
from app.models.urun_sinifi import UrunSinifi
from app.models.urun_istasyon import UrunIstasyon
from app.services.islem_log_service import islem_logla_veri


def _metin(deger):
    return str(deger or "").strip()


def _istasyon_kodlarini_ayir(deger) -> list[str]:
    return list(dict.fromkeys(kod.strip() for kod in _metin(deger).replace(";", ",").split(",") if kod.strip()))


def _sirali_kod(kullanilan: set[str], onek: str) -> str:
    en_yuksek = max((int(k[len(onek):]) for k in kullanilan if k and k.startswith(onek) and k[len(onek):].isdigit()), default=0)
    sira = en_yuksek + 1
    kod = f"{onek}{sira:06}"
    while kod in kullanilan:
        sira += 1
        kod = f"{onek}{sira:06}"
    kullanilan.add(kod)
    return kod


def _sistem_kaydi_daha_yeni(kayit, satir: dict) -> bool:
    """Excel indirildikten sonra sistemde değişen mevcut kaydı korur."""
    referans = _metin(satir.get("_excel_referans_zamani"))
    guncelleme = getattr(kayit, "updated_at", None)
    if not referans or not guncelleme:
        return False
    try:
        return guncelleme > datetime.fromisoformat(referans.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return False


def _alanlari_uygula(kayit, degerler: dict) -> bool:
    """Yalnız gerçekten değişen alanları yazar."""
    degisti = False
    for alan, deger in degerler.items():
        if getattr(kayit, alan) != deger:
            setattr(kayit, alan, deger)
            degisti = True
    return degisti


def onizleme_hazirla(
    db: Session, dosya_adi: str, musteriler: list, urunler: list, personeller: list,
    istasyonlar: list, makineler: list, hatalar: list[str], eski_token: str | None,
    kullanici_adi: str, ip_adresi: str,
) -> dict:
    mevcut_istasyonlar = {i.kodu for i in db.query(Istasyon).all()}
    aktarilan_istasyonlar = {_metin(i["İstasyon Kodu"]) for i in istasyonlar}
    for sira, personel in enumerate(personeller, start=2):
        for kod in _istasyon_kodlarini_ayir(personel.get("İstasyon Kodları")):
            if kod not in mevcut_istasyonlar | aktarilan_istasyonlar:
                hatalar.append(f"Personeller satır {sira}: '{kod}' istasyon kodu bulunamadı")
    for sira, makine in enumerate(makineler, start=2):
        kod = _metin(makine["İstasyon Kodu"])
        if kod not in mevcut_istasyonlar | aktarilan_istasyonlar:
            hatalar.append(f"Makineler satır {sira}: '{kod}' istasyon kodu bulunamadı")

    stok_turleri = {tur.adi.casefold() for tur in db.query(StokUrunTuru).filter(StokUrunTuru.aktif.is_(True), StokUrunTuru.uretilen.is_(False)).all()}
    urun_siniflari = db.query(UrunSinifi).filter(UrunSinifi.aktif.is_(True)).all()
    urun_sinifi_anahtarlari = {
        anahtar.casefold()
        for sinif in urun_siniflari
        for anahtar in (sinif.kodu, sinif.adi, f"{sinif.kodu} · {sinif.adi}")
        if anahtar
    }
    if urunler and not stok_turleri:
        hatalar.append("Hammadde aktarımından önce sistemde hammadde türleri tanımlanmalıdır.")
    for sira, urun in enumerate(urunler, start=2):
        tur_adi = _metin(urun.get("stok_turu_adi"))
        sinif_anahtari = _metin(urun.get("urun_sinifi_anahtari"))
        if tur_adi.casefold() not in stok_turleri:
            hatalar.append(f"Hammaddeler satır {sira}: '{tur_adi}' türü sistemde tanımlı değil")
        if sinif_anahtari and sinif_anahtari.casefold() not in urun_sinifi_anahtarlari:
            hatalar.append(f"Hammaddeler satır {sira}: '{sinif_anahtari}' ürün sınıfı Stok/Üretim Tanımları içinde bulunamadı")
        for kod in _istasyon_kodlarini_ayir(urun.get("istasyon_kodlari")):
            if kod not in mevcut_istasyonlar | aktarilan_istasyonlar:
                hatalar.append(f"Hammaddeler satır {sira}: '{kod}' istasyon kodu bulunamadı")

    mevcut_musteriler = {m.firma_adi.casefold() for m in db.query(Musteri).all()}
    eklenecek, guncellenecek = [], []
    for satir in musteriler:
        hedef = guncellenecek if satir["Firma Adı"].casefold() in mevcut_musteriler else eklenecek
        hedef.append(satir["Firma Adı"])
    if not hatalar and not any((musteriler, urunler, personeller, istasyonlar, makineler)):
        hatalar.append("Aktarılacak veri bulunamadı.")

    token = None
    if hatalar:
        islem_logla_veri(db, kullanici_adi, ip_adresi, "Excel", "Excel önizlemesi geçersiz", f"Dosya: {dosya_adi}. {len(hatalar)} doğrulama hatası bulundu.", commit=True)
    else:
        if eski_token:
            db.query(ExcelAktarimTaslagi).filter(ExcelAktarimTaslagi.token == eski_token).delete()
        token = secrets.token_urlsafe(32)
        db.add(ExcelAktarimTaslagi(token=token, veri=json.dumps({
            "musteriler": musteriler, "urunler": urunler, "personeller": personeller,
            "istasyonlar": istasyonlar, "makineler": makineler, "dosya_adi": dosya_adi,
        }, ensure_ascii=False)))
        islem_logla_veri(db, kullanici_adi, ip_adresi, "Excel", "Excel önizlemesi hazır",
            f"Dosya: {dosya_adi}. {len(musteriler)} müşteri, {len(urunler)} stok ürünü, {len(personeller)} personel, {len(istasyonlar)} istasyon ve {len(makineler)} makine onay bekliyor.")
        db.commit()
    return {"hatalar": hatalar, "eklenecek": eklenecek, "guncellenecek": guncellenecek,
        "gecerli_satir": len(musteriler), "gecerli_urun": len(urunler), "gecerli_personel": len(personeller),
        "gecerli_istasyon": len(istasyonlar), "gecerli_makine": len(makineler), "token": token}


def onizleme_hatasini_logla(db: Session, dosya_adi: str, hata: Exception, kullanici_adi: str, ip_adresi: str):
    islem_logla_veri(db, kullanici_adi, ip_adresi, "Excel", "Excel önizlemesi başarısız",
        f"Dosya: {dosya_adi}. Hata: {type(hata).__name__}: {hata}", commit=True)


def aktarimi_onayla(db: Session, token: str | None, kullanici_adi: str, ip_adresi: str) -> bool:
    taslak = db.query(ExcelAktarimTaslagi).filter(ExcelAktarimTaslagi.token == token).first() if token else None
    aktarim = json.loads(taslak.veri) if taslak else {}
    musteriler, urunler = aktarim.get("musteriler", []), aktarim.get("urunler", [])
    personeller, istasyonlar = aktarim.get("personeller", []), aktarim.get("istasyonlar", [])
    makineler, dosya_adi = aktarim.get("makineler", []), aktarim.get("dosya_adi", "adsız dosya")
    if not any((musteriler, urunler, personeller, istasyonlar, makineler)):
        islem_logla_veri(db, kullanici_adi, ip_adresi, "Excel", "Excel aktarımı başarısız",
            "Onaylanacak geçerli veri bulunamadı; önizleme süresi dolmuş veya dosya geçersiz.", commit=True)
        return False
    try:
        kullanilan = {kod for (kod,) in db.query(Musteri.musteri_kodu).all() if kod}
        harita = {m.firma_adi.casefold(): m for m in db.query(Musteri).all() if m.firma_adi}
        for satir in musteriler:
            anahtar = satir["Firma Adı"].casefold()
            musteri = harita.get(anahtar)
            if musteri and _sistem_kaydi_daha_yeni(musteri, satir):
                continue
            if not musteri:
                musteri = Musteri(musteri_kodu=_sirali_kod(kullanilan, "M"))
                db.add(musteri); harita[anahtar] = musteri
            _alanlari_uygula(musteri, {"firma_adi": satir["Firma Adı"], "yetkili": satir["Yetkili"],
                "telefon": satir["Telefon"], "email": satir["E-Posta"], "vergi_dairesi": satir["Vergi Dairesi"],
                "vergi_no": satir["Vergi No"], "il": satir["İl"], "ilce": satir["İlçe"],
                "musteri_turu": satir["Müşteri Türü"], "adres": satir["Adres"], "aciklama": satir["Açıklama"],
                "aktif": satir["Durum"] == "Aktif"})

        kullanilan = {kod for (kod,) in db.query(Personel.kodu).all() if kod}
        harita = {p.ad_soyad.casefold(): p for p in db.query(Personel).all() if p.ad_soyad}
        yeni_personel_anahtarlari = set()
        for satir in personeller:
            ad = _metin(satir["Ad Soyad"]); anahtar = ad.casefold(); personel = harita.get(anahtar)
            if personel and _sistem_kaydi_daha_yeni(personel, satir):
                continue
            if not personel:
                personel = Personel(kodu=_sirali_kod(kullanilan, "P")); db.add(personel); harita[anahtar] = personel
                yeni_personel_anahtarlari.add(anahtar)
            _alanlari_uygula(personel, {"ad_soyad": ad, "gorev": _metin(satir["Görev"]), "aktif": _metin(satir["Durum"]) == "Aktif"})

        istasyon_haritasi = {i.kodu: i for i in db.query(Istasyon).all()}
        kullanilan_istasyon_kodlari = set(istasyon_haritasi)
        for satir in istasyonlar:
            kod = _metin(satir["İstasyon Kodu"]) or _sirali_kod(kullanilan_istasyon_kodlari, "IST-")
            satir["İstasyon Kodu"] = kod
            istasyon = istasyon_haritasi.get(kod)
            if istasyon and _sistem_kaydi_daha_yeni(istasyon, satir):
                continue
            if not istasyon:
                istasyon = Istasyon(kodu=kod); db.add(istasyon); istasyon_haritasi[kod] = istasyon
            _alanlari_uygula(istasyon, {"adi": _metin(satir["İstasyon Adı"]), "bolum": _metin(satir["Bölüm"]),
                "aciklama": _metin(satir["Açıklama"]), "aktif": _metin(satir["Durum"]) == "Aktif"})
        db.flush()

        for satir in personeller:
            personel_anahtari = _metin(satir["Ad Soyad"]).casefold()
            personel = harita.get(personel_anahtari)
            if not personel or (personel_anahtari not in yeni_personel_anahtarlari and _sistem_kaydi_daha_yeni(personel, satir)):
                continue
            secili_kodlar = _istasyon_kodlarini_ayir(satir.get("İstasyon Kodları"))
            secili_idler = {istasyon_haritasi[kod].id for kod in secili_kodlar if kod in istasyon_haritasi}
            mevcut_atamalar = {
                atama.istasyon_id: atama
                for atama in db.query(PersonelIstasyon).filter(PersonelIstasyon.personel_id == personel.id).all()
            }
            for istasyon_id, atama in mevcut_atamalar.items():
                atama.aktif = istasyon_id in secili_idler
            for istasyon_id in secili_idler - set(mevcut_atamalar):
                db.add(PersonelIstasyon(personel_id=personel.id, istasyon_id=istasyon_id, aktif=True))

        makine_haritasi = {m.kodu: m for m in db.query(Makine).all()}
        kullanilan_makine_kodlari = set(makine_haritasi)
        for satir in makineler:
            kod = _metin(satir["Makine Kodu"]) or _sirali_kod(kullanilan_makine_kodlari, "MKN-")
            satir["Makine Kodu"] = kod
            istasyon = istasyon_haritasi.get(_metin(satir["İstasyon Kodu"]))
            if not istasyon:
                raise ValueError(f"{kod} makinesi için istasyon bulunamadı")
            makine = makine_haritasi.get(kod)
            if makine and _sistem_kaydi_daha_yeni(makine, satir):
                continue
            if not makine:
                makine = Makine(kodu=kod); db.add(makine); makine_haritasi[kod] = makine
            _alanlari_uygula(makine, {"adi": _metin(satir["Makine Adı"]), "istasyon_id": istasyon.id,
                "model": _metin(satir["Model"]), "kapasite": _metin(satir["Kapasite"]),
                "aktif": _metin(satir["Durum"]) == "Aktif"})

        urun_haritasi = {u.kodu: u for u in db.query(Urun).all()}
        kullanilan_urun_kodlari = set(urun_haritasi)
        stok_turu_haritasi = {tur.adi.casefold(): tur for tur in db.query(StokUrunTuru).filter(StokUrunTuru.aktif.is_(True), StokUrunTuru.uretilen.is_(False)).all()}
        urun_sinifi_haritasi = {
            anahtar.casefold(): sinif
            for sinif in db.query(UrunSinifi).filter(UrunSinifi.aktif.is_(True)).all()
            for anahtar in (sinif.kodu, sinif.adi, f"{sinif.kodu} · {sinif.adi}")
            if anahtar
        }
        for veri in urunler:
            satir = dict(veri)
            if not _metin(satir.get("kodu")):
                satir["kodu"] = _sirali_kod(kullanilan_urun_kodlari, "STK-")
            urun = urun_haritasi.get(satir["kodu"])
            if urun and _sistem_kaydi_daha_yeni(urun, satir):
                continue
            if not urun:
                urun = Urun(kodu=satir["kodu"]); db.add(urun); urun_haritasi[satir["kodu"]] = urun
            tur_adi = _metin(satir.pop("stok_turu_adi", "")).casefold()
            sinif_anahtari = _metin(satir.pop("urun_sinifi_anahtari", "")).casefold()
            secili_istasyon_kodlari = _istasyon_kodlarini_ayir(satir.pop("istasyon_kodlari", ""))
            satir.pop("_excel_referans_zamani", None)
            if tur_adi not in stok_turu_haritasi or (sinif_anahtari and sinif_anahtari not in urun_sinifi_haritasi):
                raise ValueError(f"{urun.kodu} için hammadde türü veya ürün sınıfı bulunamadı")
            _alanlari_uygula(urun, {"stok_urun_turu_id": stok_turu_haritasi[tur_adi].id,
                "urun_sinifi_id": urun_sinifi_haritasi[sinif_anahtari].id if sinif_anahtari else None,
                **satir})
            db.flush()
            secili_istasyon_idleri = {istasyon_haritasi[kod].id for kod in secili_istasyon_kodlari}
            mevcut_atamalar = {
                atama.istasyon_id: atama
                for atama in db.query(UrunIstasyon).filter(UrunIstasyon.urun_id == urun.id).all()
            }
            for istasyon_id, atama in mevcut_atamalar.items():
                atama.aktif = istasyon_id in secili_istasyon_idleri
            for istasyon_id in secili_istasyon_idleri - set(mevcut_atamalar):
                db.add(UrunIstasyon(urun_id=urun.id, istasyon_id=istasyon_id, aktif=True))
        db.delete(taslak)
        islem_logla_veri(db, kullanici_adi, ip_adresi, "Excel", "Excel aktarımı tamamlandı",
            f"Dosya: {dosya_adi}. {len(musteriler)} müşteri, {len(urunler)} stok ürünü, {len(personeller)} personel, {len(istasyonlar)} istasyon ve {len(makineler)} makine aktarıldı/güncellendi.")
        db.commit()
        return True
    except Exception as hata:
        db.rollback()
        islem_logla_veri(db, kullanici_adi, ip_adresi, "Excel", "Excel aktarımı başarısız",
            f"Dosya: {dosya_adi}. Hata: {type(hata).__name__}: {hata}", commit=True)
        return False
