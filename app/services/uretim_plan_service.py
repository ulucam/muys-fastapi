from datetime import datetime

from sqlalchemy.orm import Session

from app.models.istasyon import Istasyon
from app.models.recete import Recete
from app.models.recete_asama import ReceteAsama, ReceteAsamaMalzeme
from app.models.siparis_kalem import SiparisKalem
from app.models.siparis import Siparis
from app.models.stok_hareket import StokHareket
from app.models.uretim_emri import UretimEmri
from app.models.uretim_kaydi import UretimKaydi
from app.models.uretim_plani import UretimPlani, UretimPlanAsamasi
from app.models.urun import Urun
from app.models.stok_urun_turu import StokUrunTuru
from app.product_types import urun_turunu_normalize_et


def uretilebilir_urun_mu(urun: Urun, uretim_stok_tur_idleri: set[int] | None = None) -> bool:
    """Eski kayıtların Türkçe tür yazımlarını da üretilebilir kabul eder."""
    tur = urun_turunu_normalize_et(urun.urun_tipi)
    return tur in {"Mamül", "Yarı Mamül"} or (
        uretim_stok_tur_idleri is not None and urun.stok_urun_turu_id in uretim_stok_tur_idleri
    )


def _uretim_stok_tur_idleri(db: Session) -> set[int]:
    """Eski stok kartlarında üretim bilgisi stok türünde tutulmuş olabilir."""
    return {
        tur_id for (tur_id,) in db.query(StokUrunTuru.id).filter(
            StokUrunTuru.uretilen.is_(True), StokUrunTuru.aktif.isnot(False)
        ).all()
    }


def uretim_tanim_verisi(db: Session) -> dict:
    receteler = db.query(Recete).filter(Recete.aktif.is_(True)).order_by(Recete.updated_at.desc()).all()
    asamalar = db.query(ReceteAsama).filter(ReceteAsama.aktif.is_(True)).order_by(ReceteAsama.recete_id, ReceteAsama.sira_no).all()
    malzemeler = db.query(ReceteAsamaMalzeme).order_by(ReceteAsamaMalzeme.asama_id, ReceteAsamaMalzeme.id).all()
    # Eski veritabanlarında aktif sütunu boş kalmış ürünler üretilebilir kabul edilir;
    # yalnızca açıkça pasife alınan kartlar listeden çıkarılır.
    aktif_urunler = db.query(Urun).filter(Urun.aktif.isnot(False)).order_by(Urun.adi).all()
    uretim_stok_tur_idleri = _uretim_stok_tur_idleri(db)
    return {
        "uretim_receteleri": receteler,
        "recete_asamalari": asamalar,
        "asama_malzemeleri": malzemeler,
        "tum_urunler": aktif_urunler,
        "uretilebilir_urunler": [urun for urun in aktif_urunler if uretilebilir_urun_mu(urun, uretim_stok_tur_idleri)],
        "aktif_istasyonlar": db.query(Istasyon).filter(Istasyon.aktif.is_(True)).order_by(Istasyon.adi).all(),
        "urun_haritasi": {u.id: u for u in db.query(Urun).all()},
        "istasyon_haritasi": {i.id: i for i in db.query(Istasyon).all()},
        "siradaki_recete_no": _siradaki_recete_no(db),
    }


def _siradaki_recete_no(db: Session) -> str:
    numaralar = []
    for (recete_no,) in db.query(Recete.recete_no).all():
        if recete_no and recete_no.startswith("RCT") and recete_no[3:].isdigit():
            numaralar.append(int(recete_no[3:]))
    sira = max(numaralar, default=0) + 1
    recete_no = f"RCT{sira:06d}"
    while db.query(Recete.id).filter(Recete.recete_no == recete_no).first():
        sira += 1
        recete_no = f"RCT{sira:06d}"
    return recete_no


def recete_kaydet(db: Session, urun_id: int, tahmini_uretim_suresi: float = 0, aciklama: str = "") -> tuple[Recete, bool]:
    urun = db.query(Urun).filter(Urun.id == urun_id, Urun.aktif.isnot(False)).first()
    if not urun or not uretilebilir_urun_mu(urun, _uretim_stok_tur_idleri(db)):
        raise ValueError("Reçete çıktısı yarı mamul veya mamul olmalıdır")
    recete = db.query(Recete).filter(Recete.urun_id == urun.id, Recete.aktif.is_(True)).first()
    urun.tahmini_uretim_suresi = max(0, tahmini_uretim_suresi)
    mevcut_recete = recete is not None
    if recete:
        recete.aciklama = aciklama.strip()[:250]
    else:
        recete = Recete(urun_id=urun.id, recete_no=_siradaki_recete_no(db)[:50], aciklama=aciklama.strip()[:250], aktif=True)
    db.add(recete); db.commit()
    return recete, mevcut_recete


def _recete_toplam_suresini_guncelle(db: Session, recete_id: int) -> float:
    recete = db.query(Recete).filter(Recete.id == recete_id).first()
    if not recete:
        return 0
    toplam = sum(asama.hedef_cevrim_suresi or 0 for asama in db.query(ReceteAsama).filter(
        ReceteAsama.recete_id == recete.id, ReceteAsama.aktif.is_(True)
    ).all())
    urun = db.query(Urun).filter(Urun.id == recete.urun_id).first()
    if urun:
        urun.tahmini_uretim_suresi = toplam
    return toplam


def recete_asamasi_kaydet(db: Session, recete_id: int, sira_no: int, istasyon_id: int, operasyon_adi: str, hedef_cevrim_suresi: float = 0, aciklama: str = "") -> ReceteAsama:
    recete = db.query(Recete).filter(Recete.id == recete_id, Recete.aktif.is_(True)).first()
    istasyon = db.query(Istasyon).filter(Istasyon.id == istasyon_id, Istasyon.aktif.is_(True)).first()
    operasyon_adi = operasyon_adi.strip()
    if not recete or not istasyon or sira_no < 1 or not operasyon_adi:
        raise ValueError("Geçerli reçete, sıra, istasyon ve işlem zorunludur")
    if db.query(ReceteAsama).filter(ReceteAsama.recete_id == recete.id, ReceteAsama.sira_no == sira_no).first():
        raise ValueError("Bu sıra numarası reçetede kullanılıyor")
    asama = ReceteAsama(recete_id=recete.id, sira_no=sira_no, istasyon_id=istasyon.id,
        operasyon_adi=operasyon_adi[:150], hedef_cevrim_suresi=max(0, hedef_cevrim_suresi), aciklama=aciklama.strip()[:500])
    db.add(asama); db.flush(); _recete_toplam_suresini_guncelle(db, recete.id); db.commit()
    return asama


def asama_malzemesi_kaydet(db: Session, asama_id: int, malzeme_id: int, miktar: float, birim: str, fire_orani: float = 0) -> ReceteAsamaMalzeme:
    asama = db.query(ReceteAsama).filter(ReceteAsama.id == asama_id, ReceteAsama.aktif.is_(True)).first()
    malzeme = db.query(Urun).filter(Urun.id == malzeme_id, Urun.aktif.is_(True)).first()
    if not asama or not malzeme or miktar <= 0:
        raise ValueError("Aşama, malzeme ve pozitif miktar zorunludur")
    kayit = db.query(ReceteAsamaMalzeme).filter(ReceteAsamaMalzeme.asama_id == asama.id, ReceteAsamaMalzeme.malzeme_id == malzeme.id).first()
    kayit = kayit or ReceteAsamaMalzeme(asama_id=asama.id, malzeme_id=malzeme.id)
    secili_birim = birim.strip()
    if secili_birim not in {"Adet", "Kg"}:
        raise ValueError("Birim Adet veya Kg olmalıdır")
    if secili_birim == "Adet" and not float(miktar).is_integer():
        raise ValueError("Adet birimli malzeme miktarı tam sayı olmalıdır")
    kayit.miktar, kayit.birim, kayit.fire_orani = miktar, secili_birim, max(0, fire_orani)
    db.add(kayit); db.commit()
    return kayit


def recete_duzenleme_verisi(db: Session, recete_id: int) -> dict | None:
    recete = db.query(Recete).filter(Recete.id == recete_id, Recete.aktif.is_(True)).first()
    if not recete:
        return None
    asamalar = db.query(ReceteAsama).filter(ReceteAsama.recete_id == recete.id).order_by(ReceteAsama.sira_no).all()
    malzemeler = db.query(ReceteAsamaMalzeme).filter(
        ReceteAsamaMalzeme.asama_id.in_([asama.id for asama in asamalar]) if asamalar else False
    ).all() if asamalar else []
    return {
        "recete": recete,
        "asamalar": asamalar,
        "malzemeler": malzemeler,
        "urunler": db.query(Urun).filter(Urun.aktif.isnot(False)).order_by(Urun.adi).all(),
        "uretilebilir_urunler": [urun for urun in db.query(Urun).filter(Urun.aktif.isnot(False)).order_by(Urun.adi).all() if uretilebilir_urun_mu(urun, _uretim_stok_tur_idleri(db))],
        "istasyonlar": db.query(Istasyon).filter(Istasyon.aktif.is_(True)).order_by(Istasyon.adi).all(),
        "toplam_tahmini_sure": _recete_toplam_suresini_guncelle(db, recete.id),
    }


def recete_guncelle(db: Session, recete_id: int, urun_id: int, tahmini_uretim_suresi: float, aciklama: str) -> Recete:
    recete = db.query(Recete).filter(Recete.id == recete_id, Recete.aktif.is_(True)).first()
    urun = db.query(Urun).filter(Urun.id == urun_id, Urun.aktif.isnot(False)).first()
    cakisan = db.query(Recete).filter(Recete.urun_id == urun_id, Recete.id != recete_id, Recete.aktif.is_(True)).first()
    if not recete or not urun or not uretilebilir_urun_mu(urun, _uretim_stok_tur_idleri(db)) or cakisan:
        raise ValueError("Geçerli ve başka aktif reçetesi olmayan bir üretim ürünü seçin")
    recete.urun_id, recete.aciklama = urun.id, aciklama.strip()[:250]
    urun.tahmini_uretim_suresi = max(0, tahmini_uretim_suresi)
    _recete_toplam_suresini_guncelle(db, recete_id); db.commit()
    return recete


def recete_asamasi_guncelle(db: Session, recete_id: int, asama_id: int, sira_no: int, istasyon_id: int, operasyon_adi: str, hedef_cevrim_suresi: float, aciklama: str) -> ReceteAsama:
    asama = db.query(ReceteAsama).filter(ReceteAsama.id == asama_id, ReceteAsama.recete_id == recete_id).first()
    istasyon = db.query(Istasyon).filter(Istasyon.id == istasyon_id, Istasyon.aktif.is_(True)).first()
    cakisan = db.query(ReceteAsama).filter(ReceteAsama.recete_id == recete_id, ReceteAsama.sira_no == sira_no, ReceteAsama.id != asama_id).first()
    if not asama or not istasyon or sira_no < 1 or not operasyon_adi.strip() or cakisan:
        raise ValueError("Aşama sıra, istasyon ve operasyon bilgilerini kontrol edin")
    asama.sira_no, asama.istasyon_id = sira_no, istasyon.id
    asama.operasyon_adi, asama.hedef_cevrim_suresi = operasyon_adi.strip()[:150], max(0, hedef_cevrim_suresi)
    asama.aciklama = aciklama.strip()[:500]
    _recete_toplam_suresini_guncelle(db, recete_id); db.commit()
    return asama


def recete_asamasi_sil(db: Session, recete_id: int, asama_id: int) -> None:
    asama = db.query(ReceteAsama).filter(ReceteAsama.id == asama_id, ReceteAsama.recete_id == recete_id).first()
    if not asama:
        raise ValueError("Reçete aşaması bulunamadı")
    db.query(ReceteAsamaMalzeme).filter(ReceteAsamaMalzeme.asama_id == asama.id).delete()
    db.delete(asama)
    db.flush(); _recete_toplam_suresini_guncelle(db, recete_id); db.commit()


def asama_malzemesi_sil(db: Session, asama_id: int, malzeme_id: int) -> None:
    kayit = db.query(ReceteAsamaMalzeme).filter(
        ReceteAsamaMalzeme.asama_id == asama_id, ReceteAsamaMalzeme.malzeme_id == malzeme_id
    ).first()
    if not kayit:
        raise ValueError("Aşama malzemesi bulunamadı")
    db.delete(kayit)
    db.commit()


def _siradaki_plan_no(db: Session) -> str:
    return f"UP-{datetime.now():%Y%m%d}-{db.query(UretimPlani).count() + 1:04d}"


def uretim_plani_olustur(db: Session, recete_id: int, miktar: float, hedef_turu: str, siparis_kalem_id: int | None = None, aciklama: str = "") -> UretimPlani:
    recete = db.query(Recete).filter(Recete.id == recete_id, Recete.aktif.is_(True)).first()
    asamalar = db.query(ReceteAsama).filter(ReceteAsama.recete_id == recete_id, ReceteAsama.aktif.is_(True)).order_by(ReceteAsama.sira_no).all()
    hedef_turu = hedef_turu.strip().title()
    siparis_kalemi = db.query(SiparisKalem).filter(SiparisKalem.id == siparis_kalem_id, SiparisKalem.aktif.is_(True)).first() if siparis_kalem_id else None
    if not recete or not asamalar or miktar <= 0 or hedef_turu not in {"Siparis", "Stok"}:
        raise ValueError("Aşamalı reçete, hedef ve pozitif miktar zorunludur")
    if hedef_turu == "Siparis" and (not siparis_kalemi or siparis_kalemi.urun_id != recete.urun_id):
        raise ValueError("Reçete ürünüyle eşleşen sipariş kalemi seçilmelidir")
    urun = db.query(Urun).filter(Urun.id == recete.urun_id).first()
    if urun and urun.birim == "Adet" and not float(miktar).is_integer():
        raise ValueError("Adet birimli üretim miktarı tam sayı olmalıdır")
    plan = UretimPlani(plan_no=_siradaki_plan_no(db), hedef_turu=hedef_turu,
        siparis_kalem_id=siparis_kalemi.id if siparis_kalemi else None, urun_id=recete.urun_id,
        recete_id=recete.id, miktar=miktar, durum="Hazır", aciklama=aciklama.strip()[:500])
    db.add(plan); db.flush()
    for index, asama in enumerate(asamalar):
        plan_asamasi = UretimPlanAsamasi(uretim_plani_id=plan.id, recete_asama_id=asama.id,
            sira_no=asama.sira_no, istasyon_id=asama.istasyon_id, operasyon_adi=asama.operasyon_adi,
            hedef_miktar=miktar, durum="Hazır" if index == 0 else "Bekliyor")
        db.add(plan_asamasi); db.flush()
        db.add(UretimEmri(emir_no=f"{plan.plan_no}-{asama.sira_no:02d}", siparis_kalem_id=plan.siparis_kalem_id,
            urun_id=plan.urun_id, miktar=miktar, durum="Planlandı" if index == 0 else "Sırada",
            aciklama=asama.operasyon_adi, aktif=index == 0, istasyon_id=asama.istasyon_id,
            uretim_plani_id=plan.id, plan_asamasi_id=plan_asamasi.id))
    db.commit()
    return plan


def urun_icin_uretim_plani_olustur(
    db: Session, urun_id: int, miktar: float, hedef_turu: str,
    siparis_kalem_id: int | None = None, aciklama: str = "",
) -> UretimPlani:
    """Planlamada reçeteyi kullanıcıya seçtirmeden ürünün aktif reçetesini kullanır."""
    recete = db.query(Recete).filter(Recete.urun_id == urun_id, Recete.aktif.is_(True)).first()
    if not recete:
        raise ValueError("Seçilen ürün için aktif üretim reçetesi bulunamadı")
    return uretim_plani_olustur(db, recete.id, miktar, hedef_turu, siparis_kalem_id, aciklama)


def secimden_uretim_plani_olustur(
    db: Session, hedef_turu: str, miktar: float, siparis_kalem_id: int | None,
    stok_urun_id: int | None, aciklama: str = "",
) -> UretimPlani:
    """Sipariş kalemi veya stok ürünü seçimine göre doğru reçeteyi çözer."""
    if hedef_turu == "Siparis":
        kalem = db.query(SiparisKalem).filter(SiparisKalem.id == siparis_kalem_id, SiparisKalem.aktif.is_(True)).first()
        if not kalem:
            raise ValueError("Geçerli bir sipariş kalemi seçin")
        return urun_icin_uretim_plani_olustur(db, kalem.urun_id, miktar, hedef_turu, kalem.id, aciklama)
    return urun_icin_uretim_plani_olustur(db, stok_urun_id or 0, miktar, hedef_turu, None, aciklama)


def uretim_planini_iptal_et(db: Session, plan_id: int) -> UretimPlani:
    """İptalde ara çıktıyı ilgili operasyonun yarı mamul kartına aktarır."""
    plan = db.query(UretimPlani).filter(UretimPlani.id == plan_id, UretimPlani.aktif.is_(True)).first()
    if not plan or plan.durum == "Tamamlandı":
        raise ValueError("İptal edilecek aktif üretim planı bulunamadı")
    emirler = db.query(UretimEmri).filter(UretimEmri.uretim_plani_id == plan.id).all()
    emir_idleri = [emir.id for emir in emirler]
    aktif_kayit = db.query(UretimKaydi).filter(UretimKaydi.uretim_emri_id.in_(emir_idleri), UretimKaydi.durum == "Devam Ediyor").first() if emir_idleri else None
    asamalar = db.query(UretimPlanAsamasi).filter(UretimPlanAsamasi.uretim_plani_id == plan.id).order_by(UretimPlanAsamasi.sira_no).all()
    tamamlananlar = [asama for asama in asamalar if asama.durum == "Tamamlandı" and (asama.tamamlanan_miktar or 0) > 0]
    if aktif_kayit:
        # Operatörün başlattığı iş kesilmez; bitirdiğinde bu aşamanın çıktısı ara stoka alınır.
        plan.durum = "İptal Bekliyor"
        aktif_emir_id = aktif_kayit.uretim_emri_id
        for asama in asamalar:
            if asama.durum not in ("Tamamlandı", "Üretimde"):
                asama.durum = "İptal"
        for emir in emirler:
            if emir.id != aktif_emir_id and emir.durum != "Tamamlandı":
                emir.durum, emir.aktif = "İptal", False
        db.commit()
        return plan
    if tamamlananlar:
        _plan_ara_stoga_al(db, plan, tamamlananlar[-1], tamamlananlar[-1].tamamlanan_miktar)
    for asama in asamalar:
        if asama.durum != "Tamamlandı":
            asama.durum = "İptal"
    for emir in emirler:
        if emir.durum != "Tamamlandı":
            emir.durum, emir.aktif = "İptal", False
    plan.durum, plan.aktif = "İptal", False
    db.commit()
    return plan


def _plan_ara_stoga_al(db: Session, plan: UretimPlani, asama: UretimPlanAsamasi, miktar: float) -> None:
    """Her ürün/operasyon çifti için tek ara yarı mamul kartı kullanır."""
    if miktar <= 0:
        return
    ana_urun = db.query(Urun).filter(Urun.id == plan.urun_id).first()
    if not ana_urun:
        return
    kod = f"ARA-{plan.urun_id}-{asama.recete_asama_id}"
    ara_urun = db.query(Urun).filter(Urun.kodu == kod).first()
    if not ara_urun:
        ara_urun = Urun(kodu=kod, adi=f"{ana_urun.adi} · {asama.operasyon_adi} sonrası yarı mamul",
            urun_tipi="Yarı Mamül", birim=ana_urun.birim, aktif=True, mevcut_stok=0, min_stok=0)
        db.add(ara_urun); db.flush()
    ara_urun.mevcut_stok = (ara_urun.mevcut_stok or 0) + miktar
    db.add(StokHareket(urun_id=ara_urun.id, hareket_tipi="Giriş", miktar=miktar,
        aciklama=f"{plan.plan_no} iptal: {asama.sira_no}. aşama ({asama.operasyon_adi}) yarı mamul", referans=plan.plan_no))


def plan_asamasini_tamamla(db: Session, emir: UretimEmri, uretilen_miktar: float, fire_miktari: float) -> None:
    if not emir.plan_asamasi_id or not emir.uretim_plani_id:
        return
    plan = db.query(UretimPlani).filter(UretimPlani.id == emir.uretim_plani_id).first()
    asama = db.query(UretimPlanAsamasi).filter(UretimPlanAsamasi.id == emir.plan_asamasi_id).first()
    if not plan or not asama:
        return
    asama.tamamlanan_miktar, asama.fire_miktari = uretilen_miktar, fire_miktari
    asama.durum, asama.bitis_tarihi = "Tamamlandı", datetime.now()
    recete_malzemeleri = db.query(ReceteAsamaMalzeme).filter(ReceteAsamaMalzeme.asama_id == asama.recete_asama_id).all()
    for satir in recete_malzemeleri:
        malzeme = db.query(Urun).filter(Urun.id == satir.malzeme_id).first()
        if not malzeme:
            continue
        tuketim = satir.miktar * uretilen_miktar * (1 + (satir.fire_orani or 0) / 100)
        malzeme.mevcut_stok = (malzeme.mevcut_stok or 0) - tuketim
        db.add(StokHareket(urun_id=malzeme.id, hareket_tipi="Çıkış", miktar=tuketim,
            aciklama=f"{plan.plan_no} / {asama.operasyon_adi}", referans=plan.plan_no))
    if plan.durum == "İptal Bekliyor":
        _plan_ara_stoga_al(db, plan, asama, uretilen_miktar)
        plan.durum, plan.aktif = "İptal", False
        return
    sonraki = db.query(UretimPlanAsamasi).filter(UretimPlanAsamasi.uretim_plani_id == plan.id,
        UretimPlanAsamasi.sira_no > asama.sira_no).order_by(UretimPlanAsamasi.sira_no).first()
    if sonraki:
        sonraki.durum = "Hazır"
        sonraki_emir = db.query(UretimEmri).filter(UretimEmri.plan_asamasi_id == sonraki.id).first()
        if sonraki_emir:
            sonraki_emir.aktif, sonraki_emir.durum = True, "Planlandı"
        plan.durum = "Üretimde"
    else:
        plan.durum = "Tamamlandı"
        urun = db.query(Urun).filter(Urun.id == plan.urun_id).first()
        if plan.hedef_turu == "Stok" and urun:
            urun.mevcut_stok = (urun.mevcut_stok or 0) + uretilen_miktar
            db.add(StokHareket(urun_id=urun.id, hareket_tipi="Giriş", miktar=uretilen_miktar,
                aciklama="Stok için üretim tamamlandı", referans=plan.plan_no))
        elif plan.siparis_kalem_id:
            kalem = db.query(SiparisKalem).filter(SiparisKalem.id == plan.siparis_kalem_id).first()
            if kalem:
                kalem.uretilen_miktar = (kalem.uretilen_miktar or 0) + uretilen_miktar
                kalem.durum = "Tamamlandı" if kalem.uretilen_miktar >= kalem.miktar else "Üretimde"


def planlama_verisi(db: Session) -> dict:
    receteler = db.query(Recete).filter(Recete.aktif.is_(True)).order_by(Recete.recete_no).all()
    recete_urun_idleri = {recete.urun_id for recete in receteler}
    urunler = {u.id: u for u in db.query(Urun).all()}
    kalemler = [kalem for kalem in db.query(SiparisKalem).filter(
        SiparisKalem.aktif.is_(True), SiparisKalem.durum != "Tamamlandı"
    ).order_by(SiparisKalem.created_at.desc()).all() if kalem.urun_id in recete_urun_idleri]
    stok_uretim_urunleri = [
        urun for urun_id, urun in urunler.items() if urun_id in recete_urun_idleri and urun.aktif is not False
        and (urun_turunu_normalize_et(urun.urun_tipi) == "Mamül" or (urun.urun_tipi or "").strip().casefold() == "yedek parça")
    ]
    return {"plan_receteleri": receteler, "bekleyen_siparis_kalemleri": kalemler,
        "stok_uretim_urunleri": sorted(stok_uretim_urunleri, key=lambda urun: urun.adi.casefold()),
        "uretim_planlari": db.query(UretimPlani).filter(UretimPlani.aktif.is_(True)).order_by(UretimPlani.created_at.desc()).limit(50).all(),
        "plan_urun_haritasi": urunler,
        "plan_siparis_haritasi": {s.id: s for s in db.query(Siparis).all()}}
