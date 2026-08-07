from sqlalchemy.orm import Session

from app.models.istasyon import Istasyon
from app.models.makine import Makine
from app.models.personel import Personel
from app.models.personel_makine import PersonelMakine
from app.models.personel_istasyon import PersonelIstasyon
from app.models.puantaj import Puantaj
from app.models.recete import Recete
from app.models.recete_kalem import ReceteKalem
from app.models.urun import Urun
from app.models.urun_sinif_operasyon import UrunSinifOperasyon
from app.models.urun_sinif_operasyon_makine import UrunSinifOperasyonMakine
from app.models.urun_sinifi import UrunSinifi
from app.models.user import User
from app.services.islem_log_service import islem_logla_veri

ANA_MODELLER = {"personel": Personel, "istasyon": Istasyon, "makine": Makine, "sinif": UrunSinifi}
ILISKILI_MODELLER = {"operasyon": UrunSinifOperasyon, "urun": Urun, "recete": ReceteKalem}
URUN_TIPLERI = {"Hammadde", "YariMamul", "Mamul", "TicariMamul"}


def metin(deger):
    return str(deger or "").strip()


def sayi(deger, alan, tam_sayi=False):
    try:
        return int(deger) if tam_sayi else float(deger)
    except (TypeError, ValueError):
        raise ValueError(f"{alan} sayısal olmalı")


def ekran_verisi(db: Session, **ek) -> dict:
    atamalar = db.query(PersonelMakine).filter(PersonelMakine.aktif.is_(True)).all()
    makine_haritasi = {m.id: m for m in db.query(Makine).all()}
    personel_atamalari = {}
    for atama in atamalar:
        personel_atamalari.setdefault(atama.personel_id, []).append((atama, makine_haritasi.get(atama.makine_id)))
    istasyon_haritasi = {istasyon.id: istasyon for istasyon in db.query(Istasyon).all()}
    personel_istasyonlari = {}
    for atama in db.query(PersonelIstasyon).filter(PersonelIstasyon.aktif.is_(True)).all():
        istasyon = istasyon_haritasi.get(atama.istasyon_id)
        if istasyon:
            personel_istasyonlari.setdefault(atama.personel_id, []).append(istasyon)
    personel_puantajlari = {}
    for puantaj in db.query(Puantaj).order_by(Puantaj.tarih.desc()).limit(500).all():
        if len(personel_puantajlari.setdefault(puantaj.personel_id, [])) < 10:
            personel_puantajlari[puantaj.personel_id].append(puantaj)
    data = {
        "personel_sayisi": db.query(Personel).filter(Personel.aktif.is_(True)).count(),
        "istasyon_sayisi": db.query(Istasyon).filter(Istasyon.aktif.is_(True)).count(),
        "makine_sayisi": db.query(Makine).filter(Makine.aktif.is_(True)).count(),
        "pasif_istasyon_sayisi": db.query(Istasyon).filter(Istasyon.aktif.is_(False)).count(),
        "pasif_makine_sayisi": db.query(Makine).filter(Makine.aktif.is_(False)).count(),
        "urun_sinifi_sayisi": db.query(UrunSinifi).filter(UrunSinifi.aktif.is_(True)).count(),
        "operasyon_sayisi": db.query(UrunSinifOperasyon.urun_sinifi_id).filter(UrunSinifOperasyon.aktif.is_(True)).distinct().count(),
        "urun_sayisi": db.query(Urun).filter(Urun.aktif.is_(True)).count(),
        "recete_bileseni_sayisi": db.query(ReceteKalem).filter(ReceteKalem.aktif.is_(True)).count(),
        "istasyonlar": db.query(Istasyon).order_by(Istasyon.kodu).all(),
        "personeller": db.query(Personel).order_by(Personel.kodu).all(),
        "makineler": db.query(Makine).order_by(Makine.kodu).all(),
        "urun_siniflari": db.query(UrunSinifi).order_by(UrunSinifi.kodu).all(),
        "urunler": db.query(Urun).order_by(Urun.kodu).all(),
        "receteler": {r.id: r for r in db.query(Recete).all()},
        "personel_atamalari": personel_atamalari,
        "personel_istasyonlari": personel_istasyonlari,
        "personel_puantajlari": personel_puantajlari,
    }
    data.update(ek)
    return data


def personel_listesi_verisi(db: Session, q: str, departman: str, gorev: str, istasyon_id: int | None) -> dict:
    sorgu = db.query(Personel).filter(Personel.aktif.is_(True))
    if q.strip():
        arama = f"%{q.strip()}%"
        sorgu = sorgu.filter((Personel.ad_soyad.ilike(arama)) | (Personel.kodu.ilike(arama)))
    if departman: sorgu = sorgu.filter(Personel.departman == departman)
    if gorev: sorgu = sorgu.filter(Personel.gorev == gorev)
    if istasyon_id:
        makine_idleri = [m.id for m in db.query(Makine).filter(Makine.istasyon_id == istasyon_id).all()]
        personel_idleri = [a.personel_id for a in db.query(PersonelMakine).filter(PersonelMakine.makine_id.in_(makine_idleri), PersonelMakine.aktif.is_(True)).all()]
        personel_idleri.extend(a.personel_id for a in db.query(PersonelIstasyon).filter(PersonelIstasyon.istasyon_id == istasyon_id, PersonelIstasyon.aktif.is_(True)).all())
        sorgu = sorgu.filter(Personel.id.in_(personel_idleri))
    makine_haritasi = {m.id: m for m in db.query(Makine).all()}
    istasyon_haritasi = {i.id: i for i in db.query(Istasyon).all()}
    iliskiler = {}
    for atama in db.query(PersonelMakine).filter(PersonelMakine.aktif.is_(True)).all():
        makine = makine_haritasi.get(atama.makine_id)
        iliskiler.setdefault(atama.personel_id, []).append({"atama": atama, "makine": makine, "istasyon": istasyon_haritasi.get(makine.istasyon_id) if makine else None})
    personel_istasyonlari = {}
    for atama in db.query(PersonelIstasyon).filter(PersonelIstasyon.aktif.is_(True)).all():
        istasyon = istasyon_haritasi.get(atama.istasyon_id)
        if istasyon:
            personel_istasyonlari.setdefault(atama.personel_id, []).append(istasyon)
    return {
        "personeller": sorgu.order_by(Personel.ad_soyad).all(),
        "departmanlar": sorted({d for (d,) in db.query(Personel.departman).filter(Personel.departman != "").distinct().all()}),
        "gorevler": sorted({g for (g,) in db.query(Personel.gorev).filter(Personel.gorev != "").distinct().all()}),
        "istasyonlar": db.query(Istasyon).filter(Istasyon.aktif.is_(True)).order_by(Istasyon.kodu).all(),
        "makineler": db.query(Makine).filter(Makine.aktif.is_(True)).order_by(Makine.kodu).all(),
        "iliskiler": iliskiler,
        "personel_istasyonlari": personel_istasyonlari,
        "kullanici_haritasi": {u.personel_id: u for u in db.query(User).filter(User.personel_id.isnot(None)).all()},
        "istasyon_haritasi": istasyon_haritasi,
        "q": q, "departman": departman, "gorev": gorev, "istasyon_id": istasyon_id,
    }


def personel_istasyon_idleri(db: Session, personel_id: int) -> set[int]:
    return {
        atama.istasyon_id
        for atama in db.query(PersonelIstasyon).filter(
            PersonelIstasyon.personel_id == personel_id,
            PersonelIstasyon.aktif.is_(True),
        ).all()
    }


def personel_istasyonlarini_guncelle(db: Session, personel_id: int, istasyon_idleri) -> None:
    secilen_idler = {int(istasyon_id) for istasyon_id in istasyon_idleri if str(istasyon_id).isdigit()}
    gecerli_idler = {
        istasyon.id
        for istasyon in db.query(Istasyon).filter(Istasyon.id.in_(secilen_idler), Istasyon.aktif.is_(True)).all()
    } if secilen_idler else set()
    if gecerli_idler != secilen_idler:
        raise ValueError("Seçilen istasyonlardan biri geçerli veya aktif değil")
    mevcutlar = {
        atama.istasyon_id: atama
        for atama in db.query(PersonelIstasyon).filter(PersonelIstasyon.personel_id == personel_id).all()
    }
    for istasyon_id, atama in mevcutlar.items():
        atama.aktif = istasyon_id in secilen_idler
    for istasyon_id in secilen_idler - set(mevcutlar):
        db.add(PersonelIstasyon(personel_id=personel_id, istasyon_id=istasyon_id, aktif=True))


def personel_makine_idleri(db: Session, personel_id: int) -> set[int]:
    return {
        atama.makine_id
        for atama in db.query(PersonelMakine).filter(
            PersonelMakine.personel_id == personel_id,
            PersonelMakine.aktif.is_(True),
        ).all()
    }


def personel_makinelerini_guncelle(db: Session, personel_id: int, makine_idleri) -> None:
    secilen_idler = {int(makine_id) for makine_id in makine_idleri if str(makine_id).isdigit()}
    gecerli_idler = {
        makine.id
        for makine in db.query(Makine).filter(Makine.id.in_(secilen_idler), Makine.aktif.is_(True)).all()
    } if secilen_idler else set()
    if gecerli_idler != secilen_idler:
        raise ValueError("Seçilen makinelerden biri geçerli veya aktif değil")
    mevcutlar = {
        atama.makine_id: atama
        for atama in db.query(PersonelMakine).filter(PersonelMakine.personel_id == personel_id).all()
    }
    for makine_id, atama in mevcutlar.items():
        atama.aktif = makine_id in secilen_idler
    for makine_id in secilen_idler - set(mevcutlar):
        db.add(PersonelMakine(personel_id=personel_id, makine_id=makine_id, rol="Operatör", aktif=True))


def tanim_listesi(db: Session, goster: str):
    listeler = {
        "personeller": ("Aktif Personeller", db.query(Personel).filter(Personel.aktif.is_(True)).order_by(Personel.kodu).all()),
        "istasyonlar": ("Aktif İstasyonlar", db.query(Istasyon).filter(Istasyon.aktif.is_(True)).order_by(Istasyon.kodu).all()),
        "makineler": ("Aktif Makineler", db.query(Makine).filter(Makine.aktif.is_(True)).order_by(Makine.kodu).all()),
        "istasyonlar_pasif": ("Pasif İstasyonlar", db.query(Istasyon).filter(Istasyon.aktif.is_(False)).order_by(Istasyon.kodu).all()),
        "makineler_pasif": ("Pasif Makineler", db.query(Makine).filter(Makine.aktif.is_(False)).order_by(Makine.kodu).all()),
        "urun_siniflari": ("Aktif Ürün Sınıfları", db.query(UrunSinifi).filter(UrunSinifi.aktif.is_(True)).order_by(UrunSinifi.kodu).all()),
        "operasyonlar": ("Sınıf Reçeteleri", sinif_recetelerini_listele(db)),
        "urunler": ("Ürün Kartları", db.query(Urun).order_by(Urun.kodu).all()),
        "recete_bilesenleri": ("Ürün Reçetesi Bileşenleri", db.query(ReceteKalem).order_by(ReceteKalem.recete_id, ReceteKalem.sira_no).all()),
    }
    return listeler.get(goster, (None, []))


def sinif_recetelerini_listele(db: Session) -> list[dict]:
    """Operasyon satırlarını, kullanıcı arayüzü için ürün sınıfı bazında tek zincirde toplar."""
    siniflar = {sinif.id: sinif for sinif in db.query(UrunSinifi).order_by(UrunSinifi.kodu).all()}
    zincirler = {}
    for operasyon in db.query(UrunSinifOperasyon).order_by(UrunSinifOperasyon.urun_sinifi_id, UrunSinifOperasyon.sira_no).all():
        zincir = zincirler.setdefault(
            operasyon.urun_sinifi_id,
            {"sinif": siniflar.get(operasyon.urun_sinifi_id), "operasyonlar": []},
        )
        zincir["operasyonlar"].append(operasyon)
    return list(zincirler.values())


def sinif_recetesi_getir(db: Session, sinif_id: int):
    sinif = db.query(UrunSinifi).filter(UrunSinifi.id == sinif_id).first()
    operasyonlar = (
        db.query(UrunSinifOperasyon)
        .filter(UrunSinifOperasyon.urun_sinifi_id == sinif_id)
        .order_by(UrunSinifOperasyon.sira_no)
        .all()
        if sinif else []
    )
    makine_kodlari = {}
    for operasyon in operasyonlar:
        makine_kodlari[operasyon.id] = [
            makine.kodu
            for makine in (
                db.query(Makine)
                .join(UrunSinifOperasyonMakine, UrunSinifOperasyonMakine.makine_id == Makine.id)
                .filter(UrunSinifOperasyonMakine.operasyon_id == operasyon.id)
                .all()
            )
        ]
    return sinif, operasyonlar, makine_kodlari


def sinif_recetesi_guncelle(db: Session, sinif_id: int, form) -> bool:
    """Bir ürün sınıfının tüm operasyon zincirini tek işlemde günceller."""
    try:
        sinif = db.query(UrunSinifi).filter(UrunSinifi.id == sinif_id).first()
        operasyon_sayisi = sayi(form.get("operasyon_sayisi"), "Operasyon sayısı", tam_sayi=True)
        if not sinif or not 1 <= operasyon_sayisi <= 50:
            raise ValueError("Geçerli bir sınıf ve 1-50 arası operasyon sayısı zorunlu")

        yeni_satirlar = []
        for sira in range(1, operasyon_sayisi + 1):
            istasyon = db.query(Istasyon).filter(Istasyon.kodu == metin(form.get(f"istasyon_kodu_{sira}"))).first()
            operasyon_adi = metin(form.get(f"operasyon_adi_{sira}"))
            makine_kodlari = [metin(kod) for kod in form.getlist(f"makine_kodlari_{sira}") if metin(kod)]
            makineler = db.query(Makine).filter(Makine.kodu.in_(makine_kodlari)).all() if makine_kodlari else []
            if not istasyon or not operasyon_adi:
                raise ValueError(f"{sira}. sıra için istasyon ve operasyon adı zorunlu")
            if len(makineler) != len(set(makine_kodlari)) or any(makine.istasyon_id != istasyon.id for makine in makineler):
                raise ValueError(f"{sira}. sıradaki makineler seçilen istasyona bağlı olmalı")
            yeni_satirlar.append((sira, istasyon, operasyon_adi, makineler, metin(form.get(f"kontrol_noktasi_{sira}"))))

        mevcutlar = {
            operasyon.sira_no: operasyon
            for operasyon in db.query(UrunSinifOperasyon).filter(UrunSinifOperasyon.urun_sinifi_id == sinif.id).all()
        }
        for sira, istasyon, operasyon_adi, makineler, kontrol_noktasi in yeni_satirlar:
            operasyon = mevcutlar.pop(sira, None) or UrunSinifOperasyon(urun_sinifi_id=sinif.id, sira_no=sira)
            operasyon.istasyon_id = istasyon.id
            operasyon.makine_id = makineler[0].id if makineler else None
            operasyon.operasyon_adi = operasyon_adi
            operasyon.kontrol_noktasi = kontrol_noktasi
            operasyon.aktif = True
            db.add(operasyon)
            db.flush()
            db.query(UrunSinifOperasyonMakine).filter(UrunSinifOperasyonMakine.operasyon_id == operasyon.id).delete()
            for makine in makineler:
                db.add(UrunSinifOperasyonMakine(operasyon_id=operasyon.id, makine_id=makine.id))

        for operasyon in mevcutlar.values():
            db.query(UrunSinifOperasyonMakine).filter(UrunSinifOperasyonMakine.operasyon_id == operasyon.id).delete()
            db.delete(operasyon)
        db.commit()
        return True
    except Exception:
        db.rollback()
        return False


def ana_kayit_getir(db: Session, tip: str, kod: str):
    model = ANA_MODELLER.get(tip)
    return db.query(model).filter(model.kodu == kod).first() if model else None


def iliskili_kayit_getir(db: Session, tip: str, kayit_id: int):
    model = ILISKILI_MODELLER.get(tip)
    kayit = db.query(model).filter(model.id == kayit_id).first() if model else None
    makine_idleri = [x.makine_id for x in db.query(UrunSinifOperasyonMakine).filter(UrunSinifOperasyonMakine.operasyon_id == kayit_id).all()] if tip == "operasyon" else []
    return kayit, makine_idleri


def tanim_sil(db: Session, tip: str, kod: str) -> bool:
    model = {"istasyon": Istasyon, "makine": Makine}.get(tip)
    kayit = db.query(model).filter(model.kodu == kod).first() if model else None
    if not kayit: return False
    try:
        db.delete(kayit); db.commit()
    except Exception:
        db.rollback(); kayit = db.query(model).filter(model.kodu == kod).first()
        if kayit: kayit.aktif = False; db.commit()
    return True

def iliskili_kayit_guncelle(db: Session, tip: str, kayit_id: int, form) -> str | None:
    try:
        if tip == "operasyon":
            kayit = db.query(UrunSinifOperasyon).filter(UrunSinifOperasyon.id == kayit_id).first()
            sinif = db.query(UrunSinifi).filter(UrunSinifi.kodu == metin(form.get("sinif_kodu"))).first()
            istasyon = db.query(Istasyon).filter(Istasyon.kodu == metin(form.get("istasyon_kodu"))).first()
            makineler = db.query(Makine).filter(Makine.kodu.in_(form.getlist("makine_kodlari"))).all()
            if not kayit or not sinif or not istasyon or not metin(form.get("operasyon_adi")) or any(m.istasyon_id != istasyon.id for m in makineler):
                raise ValueError("Geçersiz operasyon bilgisi")
            kayit.urun_sinifi_id, kayit.sira_no, kayit.istasyon_id = sinif.id, sayi(form.get("sira"), "Sıra", True), istasyon.id
            kayit.operasyon_adi, kayit.kontrol_noktasi, kayit.aktif = metin(form.get("operasyon_adi")), metin(form.get("kontrol_noktasi")), form.get("aktif") == "true"
            kayit.makine_id = makineler[0].id if makineler else None
            db.query(UrunSinifOperasyonMakine).filter(UrunSinifOperasyonMakine.operasyon_id == kayit.id).delete()
            for makine in makineler:
                db.add(UrunSinifOperasyonMakine(operasyon_id=kayit.id, makine_id=makine.id))
            donus = "operasyonlar"
        elif tip == "urun":
            kayit = db.query(Urun).filter(Urun.id == kayit_id).first()
            sinif = db.query(UrunSinifi).filter(UrunSinifi.kodu == metin(form.get("sinif_kodu"))).first() if metin(form.get("sinif_kodu")) else None
            if not kayit or not metin(form.get("kodu")) or not metin(form.get("adi")) or metin(form.get("urun_tipi")) not in URUN_TIPLERI:
                raise ValueError("Geçersiz ürün bilgisi")
            cakisan = db.query(Urun).filter(Urun.kodu == metin(form.get("kodu")), Urun.id != kayit.id).first()
            if cakisan: raise ValueError("Ürün kodu kullanılıyor")
            kayit.kodu, kayit.adi, kayit.urun_tipi = metin(form.get("kodu")), metin(form.get("adi")), metin(form.get("urun_tipi"))
            birim = metin(form.get("birim")) or "Adet"
            if birim not in {"Adet", "Kg"}: raise ValueError("Birim Adet veya Kg olmalıdır")
            kayit.urun_sinifi_id, kayit.birim, kayit.urun_cinsi = sinif.id if sinif else None, birim, metin(form.get("urun_cinsi"))
            kayit.tahmini_uretim_suresi = sayi(form.get("tahmini_uretim_suresi") or 0, "Tahmini üretim süresi")
            kayit.mevcut_stok, kayit.min_stok, kayit.aktif = sayi(form.get("mevcut_stok") or 0, "Stok"), sayi(form.get("min_stok") or 0, "Min stok"), form.get("aktif") == "true"
            donus = "urunler"
        elif tip == "recete":
            kayit = db.query(ReceteKalem).filter(ReceteKalem.id == kayit_id).first()
            bilesen = db.query(Urun).filter(Urun.kodu == metin(form.get("bilesen_urun_kodu"))).first()
            if not kayit or not bilesen: raise ValueError("Bileşen bulunamadı")
            kayit.malzeme_id, kayit.miktar, kayit.birim = bilesen.id, sayi(form.get("miktar"), "Miktar"), metin(form.get("birim")) or bilesen.birim
            kayit.fire_orani, kayit.sira_no = sayi(form.get("fire_orani") or 0, "Fire"), sayi(form.get("sira") or 1, "Sıra", True)
            kayit.hedef_cevrim_suresi, kayit.aktif = sayi(form.get("hedef_cevrim") or 0, "Çevrim"), form.get("aktif") == "true"
            donus = "recete_bilesenleri"
        else: raise ValueError("Geçersiz tür")
        db.commit()
        return donus
    except Exception:
        db.rollback()
        return None


def iliskili_kayit_sil(db: Session, tip: str, kayit_id: int) -> str:
    model = ILISKILI_MODELLER.get(tip)
    kayit = db.query(model).filter(model.id == kayit_id).first() if model else None
    donus = {"operasyon": "operasyonlar", "urun": "urunler", "recete": "recete_bilesenleri"}.get(tip, "")
    if kayit:
        try:
            if tip == "operasyon":
                db.query(UrunSinifOperasyonMakine).filter(UrunSinifOperasyonMakine.operasyon_id == kayit.id).delete()
            db.delete(kayit)
            db.commit()
        except Exception:
            db.rollback()
            if tip == "urun":
                kayit = db.query(Urun).filter(Urun.id == kayit_id).first()
                if kayit:
                    kayit.aktif = False
                    db.commit()
    return donus


def manuel_tanim_kaydet(
    db: Session, tip: str, form, kullanici_rolu: str | None,
    kullanici_adi: str, ip_adresi: str,
) -> tuple[str, str | None]:
    donus = "/personeller" if form.get("donus") == "/personeller" else "/uretim-tanimlari"
    aktif = form.get("aktif") == "true"
    try:
        if tip == "personel":
            kod = metin(form.get("kodu"))
            nesne = db.query(Personel).filter(Personel.kodu == kod).first() or Personel(kodu=kod)
            if not kod or not metin(form.get("ad_soyad")):
                raise ValueError("Personel kodu ve ad soyad zorunlu")
            nesne.ad_soyad, nesne.departman, nesne.gorev, nesne.aktif = metin(form.get("ad_soyad")), metin(form.get("departman")), metin(form.get("gorev")), aktif
            db.add(nesne)
            db.flush()
            if "istasyon_idleri" in form:
                personel_istasyonlarini_guncelle(db, nesne.id, form.getlist("istasyon_idleri"))
            if "makine_idleri" in form:
                personel_makinelerini_guncelle(db, nesne.id, form.getlist("makine_idleri"))
        elif tip == "istasyon":
            kod = metin(form.get("kodu"))
            nesne = db.query(Istasyon).filter(Istasyon.kodu == kod).first() or Istasyon(kodu=kod)
            if not kod or not metin(form.get("adi")):
                raise ValueError("İstasyon kodu ve adı zorunlu")
            nesne.adi, nesne.bolum, nesne.aciklama, nesne.aktif = metin(form.get("adi")), metin(form.get("bolum")), metin(form.get("aciklama")), aktif
        elif tip == "makine":
            kod, istasyon_kodu = metin(form.get("kodu")), metin(form.get("istasyon_kodu"))
            istasyon = db.query(Istasyon).filter(Istasyon.kodu == istasyon_kodu).first()
            if not kod or not metin(form.get("adi")) or not istasyon:
                raise ValueError("Makine kodu, adı ve istasyon seçimi zorunlu")
            nesne = db.query(Makine).filter(Makine.kodu == kod).first() or Makine(kodu=kod)
            nesne.adi, nesne.istasyon_id, nesne.model, nesne.kapasite, nesne.aktif = metin(form.get("adi")), istasyon.id, metin(form.get("model")), metin(form.get("kapasite")), aktif
        elif tip == "atama":
            personel = db.query(Personel).filter(Personel.kodu == metin(form.get("personel_kodu"))).first()
            makine = db.query(Makine).filter(Makine.kodu == metin(form.get("makine_kodu"))).first()
            if not personel or not makine:
                raise ValueError("Personel ve makine seçimi zorunlu")
            nesne = db.query(PersonelMakine).filter(PersonelMakine.personel_id == personel.id, PersonelMakine.makine_id == makine.id).first() or PersonelMakine(personel_id=personel.id, makine_id=makine.id)
            nesne.rol, nesne.hedef_performans, nesne.aktif = metin(form.get("rol")) or "Operatör", sayi(form.get("hedef_performans") or 100, "Hedef performans"), aktif
        elif tip == "sinif":
            kod = metin(form.get("kodu"))
            orijinal_kodu = metin(form.get("orijinal_kodu"))
            if orijinal_kodu:
                nesne = db.query(UrunSinifi).filter(UrunSinifi.kodu == orijinal_kodu).first()
                if not nesne:
                    raise ValueError("Düzenlenecek ürün sınıfı bulunamadı")
                if kullanici_rolu != "Admin":
                    kod = orijinal_kodu
                cakisan = db.query(UrunSinifi).filter(UrunSinifi.kodu == kod, UrunSinifi.id != nesne.id).first()
                if cakisan:
                    raise ValueError("Bu ürün sınıfı kodu başka bir kayıtta kullanılıyor")
                nesne.kodu = kod
            else:
                nesne = db.query(UrunSinifi).filter(UrunSinifi.kodu == kod).first() or UrunSinifi(kodu=kod)
            if not kod or not metin(form.get("adi")):
                raise ValueError("Sınıf kodu ve adı zorunlu")
            nesne.adi, nesne.aciklama, nesne.aktif = metin(form.get("adi")), metin(form.get("aciklama")), aktif
        elif tip == "operasyon":
            sinif = db.query(UrunSinifi).filter(UrunSinifi.kodu == metin(form.get("sinif_kodu"))).first()
            operasyon_sayisi = sayi(form.get("operasyon_sayisi"), "Operasyon sayısı", tam_sayi=True)
            if not sinif or operasyon_sayisi < 1 or operasyon_sayisi > 50:
                raise ValueError("Ürün sınıfı ve 1-50 arası operasyon sayısı zorunlu")
            for sira in range(1, operasyon_sayisi + 1):
                istasyon = db.query(Istasyon).filter(Istasyon.kodu == metin(form.get(f"istasyon_kodu_{sira}"))).first()
                operasyon_adi = metin(form.get(f"operasyon_adi_{sira}"))
                if not istasyon or not operasyon_adi:
                    raise ValueError(f"{sira}. sıra için istasyon ve operasyon adı zorunlu")
                makine_kodlari = [metin(kod) for kod in form.getlist(f"makine_kodlari_{sira}") if metin(kod)]
                secili_makineler = db.query(Makine).filter(Makine.kodu.in_(makine_kodlari)).all() if makine_kodlari else []
                if any(makine.istasyon_id != istasyon.id for makine in secili_makineler) or len(secili_makineler) != len(set(makine_kodlari)):
                    raise ValueError(f"{sira}. sıradaki makineler seçilen istasyona bağlı olmalı")
                nesne = db.query(UrunSinifOperasyon).filter(UrunSinifOperasyon.urun_sinifi_id == sinif.id, UrunSinifOperasyon.sira_no == sira).first()
                if not nesne:
                    nesne = UrunSinifOperasyon(urun_sinifi_id=sinif.id, sira_no=sira)
                    db.add(nesne)
                nesne.istasyon_id = istasyon.id
                nesne.makine_id = secili_makineler[0].id if secili_makineler else None
                nesne.operasyon_adi = operasyon_adi
                nesne.hedef_cevrim_suresi = 0
                nesne.kontrol_noktasi = metin(form.get(f"kontrol_noktasi_{sira}"))
                nesne.aktif = aktif
                # Yeni operasyonun zorunlu alanları atanmadan flush edilirse
                # PostgreSQL istasyon_id için boş değer hatası verir.
                db.flush()
                db.query(UrunSinifOperasyonMakine).filter(UrunSinifOperasyonMakine.operasyon_id == nesne.id).delete()
                for makine in secili_makineler:
                    db.add(UrunSinifOperasyonMakine(operasyon_id=nesne.id, makine_id=makine.id))
        elif tip == "urun":
            kod, sinif_kodu, urun_tipi = metin(form.get("kodu")), metin(form.get("sinif_kodu")), metin(form.get("urun_tipi"))
            sinif = db.query(UrunSinifi).filter(UrunSinifi.kodu == sinif_kodu).first() if sinif_kodu else None
            if not kod or not metin(form.get("adi")) or urun_tipi not in URUN_TIPLERI or (sinif_kodu and not sinif):
                raise ValueError("Ürün kodu, adı, türü ve varsa ürün sınıfı seçimi geçerli olmalı")
            nesne = db.query(Urun).filter(Urun.kodu == kod).first() or Urun(kodu=kod)
            nesne.adi, nesne.urun_tipi, nesne.urun_sinifi_id = metin(form.get("adi")), urun_tipi, sinif.id if sinif else None
            birim = metin(form.get("birim")) or "Adet"
            if birim not in {"Adet", "Kg"}: raise ValueError("Birim Adet veya Kg olmalıdır")
            nesne.birim, nesne.mevcut_stok, nesne.min_stok = birim, sayi(form.get("mevcut_stok") or 0, "Mevcut stok"), sayi(form.get("min_stok") or 0, "Min. stok")
            nesne.tahmini_uretim_suresi = sayi(form.get("tahmini_uretim_suresi") or 0, "Tahmini üretim süresi")
            nesne.aktif = aktif
        elif tip == "recete":
            ust = db.query(Urun).filter(Urun.kodu == metin(form.get("ust_urun_kodu"))).first()
            bilesen = db.query(Urun).filter(Urun.kodu == metin(form.get("bilesen_urun_kodu"))).first()
            if not ust or not bilesen or ust.id == bilesen.id:
                raise ValueError("Geçerli ve birbirinden farklı üst ürün ile bileşen ürün seçin")
            recete = db.query(Recete).filter(Recete.urun_id == ust.id).first()
            if not recete:
                recete = Recete(urun_id=ust.id, recete_no=f"R-{ust.kodu}", aciklama=f"{ust.adi} reçetesi")
                db.add(recete)
                db.flush()
            nesne = db.query(ReceteKalem).filter(ReceteKalem.recete_id == recete.id, ReceteKalem.malzeme_id == bilesen.id).first() or ReceteKalem(recete_id=recete.id, malzeme_id=bilesen.id)
            nesne.miktar, nesne.birim, nesne.fire_orani, nesne.sira_no, nesne.aktif = sayi(form.get("miktar"), "Miktar"), metin(form.get("birim")) or bilesen.birim, sayi(form.get("fire_orani") or 0, "Fire oranı"), sayi(form.get("sira") or 1, "Sıra", tam_sayi=True), aktif
            nesne.hedef_cevrim_suresi = sayi(form.get("hedef_cevrim") or 0, "Hedef çevrim")
        else:
            raise ValueError("Bilinmeyen kayıt türü")
        if nesne not in db:
            db.add(nesne)
        islem_logla_veri(db, kullanici_adi, ip_adresi, "Üretim", "Üretim tanımı kaydedildi", tip)
        db.commit()
        return donus, None
    except Exception as hata:
        db.rollback()
        hata_mesaji = f"{type(hata).__name__}: {hata}"
        try:
            islem_logla_veri(db, kullanici_adi, ip_adresi, "Üretim", "Üretim tanımı kaydedilemedi", f"Tür: {tip}. Hata: {hata_mesaji}")
            db.commit()
        except Exception:
            db.rollback()
        return donus, hata_mesaji

def excel_verilerini_aktar(
    db: Session, veriler: dict, dosya_adi: str, kullanici_adi: str, ip_adresi: str,
) -> tuple[int, str | None]:
    try:
        personeller = {x.kodu: x for x in db.query(Personel).all()}
        for satir in veriler["Personeller"]:
            kod = metin(satir["Personel Kodu"])
            if not kod or not metin(satir["Ad Soyad"]):
                raise ValueError("Personeller: Personel Kodu ve Ad Soyad zorunlu")
            nesne = personeller.get(kod) or Personel(kodu=kod)
            nesne.ad_soyad, nesne.departman, nesne.gorev = metin(satir["Ad Soyad"]), metin(satir["Departman"]), metin(satir["Görev"])
            nesne.aktif = durum(satir["Durum"])
            if nesne not in db:
                db.add(nesne)
            personeller[kod] = nesne
        db.flush()

        istasyonlar = {x.kodu: x for x in db.query(Istasyon).all()}
        for satir in veriler["İstasyonlar"]:
            kod = metin(satir["İstasyon Kodu"])
            if not kod or not metin(satir["İstasyon Adı"]):
                raise ValueError("İstasyonlar: İstasyon Kodu ve İstasyon Adı zorunlu")
            nesne = istasyonlar.get(kod) or Istasyon(kodu=kod)
            nesne.adi, nesne.bolum, nesne.aciklama = metin(satir["İstasyon Adı"]), metin(satir["Bölüm"]), metin(satir["Açıklama"])
            nesne.aktif = durum(satir["Durum"])
            if nesne not in db:
                db.add(nesne)
            istasyonlar[kod] = nesne
        db.flush()

        makineler = {x.kodu: x for x in db.query(Makine).all()}
        for satir in veriler["Makineler"]:
            kod, istasyon_kodu = metin(satir["Makine Kodu"]), metin(satir["İstasyon Kodu"])
            if not kod or not metin(satir["Makine Adı"]) or istasyon_kodu not in istasyonlar:
                raise ValueError("Makineler: Makine Kodu, Makine Adı ve geçerli İstasyon Kodu zorunlu")
            nesne = makineler.get(kod) or Makine(kodu=kod)
            nesne.adi, nesne.istasyon_id = metin(satir["Makine Adı"]), istasyonlar[istasyon_kodu].id
            nesne.model, nesne.kapasite, nesne.aktif = metin(satir["Model"]), metin(satir["Kapasite"]), durum(satir["Durum"])
            if nesne not in db:
                db.add(nesne)
            makineler[kod] = nesne
        db.flush()

        siniflar = {x.kodu: x for x in db.query(UrunSinifi).all()}
        for satir in veriler["Ürün Sınıfları"]:
            kod = metin(satir["Sınıf Kodu"])
            if not kod or not metin(satir["Sınıf Adı"]):
                raise ValueError("Ürün Sınıfları: Sınıf Kodu ve Sınıf Adı zorunlu")
            nesne = siniflar.get(kod) or UrunSinifi(kodu=kod)
            nesne.adi, nesne.aciklama, nesne.aktif = metin(satir["Sınıf Adı"]), metin(satir["Açıklama"]), durum(satir["Durum"])
            if nesne not in db:
                db.add(nesne)
            siniflar[kod] = nesne
        db.flush()

        urunler = {x.kodu: x for x in db.query(Urun).all()}
        for satir in veriler["Ürünler"]:
            kod, sinif_kodu, urun_tipi = metin(satir["Ürün Kodu"]), metin(satir["Ürün Sınıfı Kodu"]), metin(satir["Ürün Türü"])
            if not kod or not metin(satir["Ürün Adı"]) or urun_tipi not in URUN_TIPLERI:
                raise ValueError("Ürünler: Ürün Kodu, Ürün Adı ve geçerli Ürün Türü zorunlu")
            if sinif_kodu and sinif_kodu not in siniflar:
                raise ValueError(f"Ürünler: '{sinif_kodu}' ürün sınıfı bulunamadı")
            nesne = urunler.get(kod) or Urun(kodu=kod)
            nesne.adi, nesne.urun_tipi, nesne.urun_sinifi_id = metin(satir["Ürün Adı"]), urun_tipi, siniflar[sinif_kodu].id if sinif_kodu else None
            nesne.birim = metin(satir["Birim"]) or "Adet"
            nesne.mevcut_stok = sayi(satir["Mevcut Stok"] or 0, "Mevcut Stok")
            nesne.min_stok = sayi(satir["Min. Stok"] or 0, "Min. Stok")
            nesne.max_stok = sayi(satir["Max. Stok"] or 0, "Max. Stok")
            nesne.maliyet = sayi(satir["Maliyet"] or 0, "Maliyet")
            nesne.satis_fiyati = sayi(satir["Satış Fiyatı"] or 0, "Satış Fiyatı")
            nesne.aciklama, nesne.aktif = metin(satir["Açıklama"]), durum(satir["Durum"])
            if nesne not in db:
                db.add(nesne)
            urunler[kod] = nesne
        db.flush()

        for satir in veriler["Personel Makine Atamaları"]:
            personel, makine = personeller.get(metin(satir["Personel Kodu"])), makineler.get(metin(satir["Makine Kodu"]))
            if not personel or not makine:
                raise ValueError("Personel Makine Atamaları: geçerli Personel Kodu ve Makine Kodu zorunlu")
            nesne = db.query(PersonelMakine).filter(PersonelMakine.personel_id == personel.id, PersonelMakine.makine_id == makine.id).first()
            if not nesne:
                nesne = PersonelMakine(personel_id=personel.id, makine_id=makine.id)
                db.add(nesne)
            nesne.rol, nesne.hedef_performans, nesne.aktif = metin(satir["Rol"]) or "Operatör", sayi(satir["Hedef Performans"] or 100, "Hedef Performans"), durum(satir["Durum"])

        for satir in veriler["Sınıf Reçete Operasyonları"]:
            sinif, istasyon = siniflar.get(metin(satir["Sınıf Kodu"])), istasyonlar.get(metin(satir["İstasyon Kodu"]))
            makine_kodu = metin(satir["Makine Kodu"])
            makine = makineler.get(makine_kodu) if makine_kodu else None
            if not sinif or not istasyon or not metin(satir["Operasyon Adı"]):
                raise ValueError("Sınıf Reçete Operasyonları: sınıf, istasyon ve operasyon adı zorunlu")
            if makine and makine.istasyon_id != istasyon.id:
                raise ValueError("Sınıf Reçete Operasyonları: makine seçilen istasyona bağlı olmalı")
            sira = sayi(satir["Sıra"], "Sıra", tam_sayi=True)
            nesne = db.query(UrunSinifOperasyon).filter(UrunSinifOperasyon.urun_sinifi_id == sinif.id, UrunSinifOperasyon.sira_no == sira).first()
            if not nesne:
                nesne = UrunSinifOperasyon(urun_sinifi_id=sinif.id, sira_no=sira)
                db.add(nesne)
            nesne.istasyon_id, nesne.makine_id = istasyon.id, makine.id if makine else None
            nesne.operasyon_adi = metin(satir["Operasyon Adı"])
            nesne.hedef_cevrim_suresi = 0
            nesne.kontrol_noktasi, nesne.aktif = metin(satir["Kontrol Noktası"]), durum(satir["Durum"])

        for satir in veriler["Ürün Reçetesi"]:
            ust, bilesen = urunler.get(metin(satir["Üst Ürün Kodu"])), urunler.get(metin(satir["Bileşen Ürün Kodu"]))
            if not ust or not bilesen:
                raise ValueError("Ürün Reçetesi: geçerli üst ürün ve bileşen ürün kodu zorunlu")
            recete = db.query(Recete).filter(Recete.urun_id == ust.id).first()
            if not recete:
                recete = Recete(urun_id=ust.id, recete_no=f"R-{ust.kodu}", aciklama=f"{ust.adi} reçetesi")
                db.add(recete)
                db.flush()
            kalem = db.query(ReceteKalem).filter(ReceteKalem.recete_id == recete.id, ReceteKalem.malzeme_id == bilesen.id).first()
            if not kalem:
                kalem = ReceteKalem(recete_id=recete.id, malzeme_id=bilesen.id)
                db.add(kalem)
            kalem.miktar, kalem.birim = sayi(satir["Miktar"], "Miktar"), metin(satir["Birim"]) or bilesen.birim
            kalem.fire_orani, kalem.sira_no, kalem.aktif = sayi(satir["Fire Oranı (%)"] or 0, "Fire Oranı"), sayi(satir["Sıra"], "Sıra", tam_sayi=True), True
            kalem.hedef_cevrim_suresi = sayi(satir["Hedef Çevrim Süresi (dk)"] or 0, "Hedef Çevrim Süresi")

        toplam = sum(len(satirlar) for satirlar in veriler.values())
        islem_logla_veri(db, kullanici_adi, ip_adresi, "Üretim", "Üretim ana verisi aktarıldı", f"Dosya: {dosya_adi}. {toplam} satır işlendi.")
        db.commit()
        return toplam, None
    except Exception as hata:
        db.rollback()
        islem_logla_veri(db, kullanici_adi, ip_adresi, "Üretim", "Üretim Excel aktarımı başarısız", f"Dosya: {dosya_adi}. {type(hata).__name__}: {hata}")
        db.commit()
        return 0, str(hata)


def excel_sablon_verisi(db: Session) -> dict[str, list]:
    personeller = db.query(Personel).order_by(Personel.kodu).all()
    istasyonlar = db.query(Istasyon).order_by(Istasyon.kodu).all()
    makineler = db.query(Makine).order_by(Makine.kodu).all()
    atamalar = db.query(PersonelMakine).all()
    siniflar = db.query(UrunSinifi).order_by(UrunSinifi.kodu).all()
    operasyonlar = db.query(UrunSinifOperasyon).order_by(UrunSinifOperasyon.urun_sinifi_id, UrunSinifOperasyon.sira_no).all()
    urunler = db.query(Urun).order_by(Urun.kodu).all()
    recete_kalemleri = db.query(ReceteKalem, Recete).join(Recete, ReceteKalem.recete_id == Recete.id).all()
    istasyon_kodlari = {i.id: i.kodu for i in istasyonlar}
    personel_kodlari = {p.id: p.kodu for p in personeller}
    makine_kodlari = {m.id: m.kodu for m in makineler}
    sinif_kodlari = {s.id: s.kodu for s in siniflar}
    urun_kodlari = {u.id: u.kodu for u in urunler}
    return {
        "Personeller": [[p.kodu, p.ad_soyad, p.departman, p.gorev, "Aktif" if p.aktif else "Pasif"] for p in personeller],
        "İstasyonlar": [[i.kodu, i.adi, i.bolum, i.aciklama, "Aktif" if i.aktif else "Pasif"] for i in istasyonlar],
        "Makineler": [[m.kodu, m.adi, istasyon_kodlari.get(m.istasyon_id, ""), m.model, m.kapasite, "Aktif" if m.aktif else "Pasif"] for m in makineler],
        "Personel Makine Atamaları": [[personel_kodlari.get(a.personel_id, ""), makine_kodlari.get(a.makine_id, ""), a.rol, a.hedef_performans, "Aktif" if a.aktif else "Pasif"] for a in atamalar],
        "Ürün Sınıfları": [[s.kodu, s.adi, s.aciklama, "Aktif" if s.aktif else "Pasif"] for s in siniflar],
        "Sınıf Reçete Operasyonları": [[sinif_kodlari.get(o.urun_sinifi_id, ""), o.sira_no, istasyon_kodlari.get(o.istasyon_id, ""), makine_kodlari.get(o.makine_id, ""), o.operasyon_adi, o.kontrol_noktasi, "Aktif" if o.aktif else "Pasif"] for o in operasyonlar],
        "Ürünler": [[u.kodu, u.adi, u.urun_tipi, sinif_kodlari.get(u.urun_sinifi_id, ""), u.birim, u.mevcut_stok, u.min_stok, u.max_stok, u.maliyet, u.satis_fiyati, u.aciklama, "Aktif" if u.aktif else "Pasif"] for u in urunler],
        "Ürün Reçetesi": [[urun_kodlari.get(r.urun_id, ""), urun_kodlari.get(k.malzeme_id, ""), k.miktar, k.birim, k.fire_orani, k.sira_no, k.hedef_cevrim_suresi] for k, r in recete_kalemleri],
    }


def excel_islemini_logla(db: Session, kullanici_adi: str, ip_adresi: str, islem: str, detay: str):
    islem_logla_veri(db, kullanici_adi, ip_adresi, "Üretim", islem, detay, commit=True)
