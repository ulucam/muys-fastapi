from datetime import datetime

from sqlalchemy.orm import Session

from app.models.istasyon import Istasyon
from app.models.recete import Recete
from app.models.recete_asama import ReceteAsama, ReceteAsamaMalzeme
from app.models.siparis_kalem import SiparisKalem
from app.models.siparis import Siparis
from app.models.stok_hareket import StokHareket
from app.models.uretim_emri import UretimEmri
from app.models.uretim_plani import UretimPlani, UretimPlanAsamasi
from app.models.urun import Urun


def uretim_tanim_verisi(db: Session) -> dict:
    receteler = db.query(Recete).filter(Recete.aktif.is_(True)).order_by(Recete.updated_at.desc()).all()
    asamalar = db.query(ReceteAsama).filter(ReceteAsama.aktif.is_(True)).order_by(ReceteAsama.recete_id, ReceteAsama.sira_no).all()
    malzemeler = db.query(ReceteAsamaMalzeme).order_by(ReceteAsamaMalzeme.asama_id, ReceteAsamaMalzeme.id).all()
    return {
        "uretim_receteleri": receteler,
        "recete_asamalari": asamalar,
        "asama_malzemeleri": malzemeler,
        "tum_urunler": db.query(Urun).filter(Urun.aktif.is_(True)).order_by(Urun.adi).all(),
        "uretilebilir_urunler": db.query(Urun).filter(
            Urun.aktif.is_(True), Urun.urun_tipi.in_(("YariMamul", "Mamul"))
        ).order_by(Urun.adi).all(),
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


def recete_kaydet(db: Session, urun_id: int, aciklama: str = "") -> Recete:
    urun = db.query(Urun).filter(Urun.id == urun_id, Urun.aktif.is_(True)).first()
    if not urun or urun.urun_tipi not in {"YariMamul", "Mamul"}:
        raise ValueError("Reçete çıktısı yarı mamul veya mamul olmalıdır")
    recete_no = _siradaki_recete_no(db)
    recete = Recete(urun_id=urun.id, recete_no=recete_no[:50], aciklama=aciklama.strip()[:250], aktif=True)
    db.add(recete); db.commit()
    return recete


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
    db.add(asama); db.commit()
    return asama


def asama_malzemesi_kaydet(db: Session, asama_id: int, malzeme_id: int, miktar: float, birim: str, fire_orani: float = 0) -> ReceteAsamaMalzeme:
    asama = db.query(ReceteAsama).filter(ReceteAsama.id == asama_id, ReceteAsama.aktif.is_(True)).first()
    malzeme = db.query(Urun).filter(Urun.id == malzeme_id, Urun.aktif.is_(True)).first()
    if not asama or not malzeme or miktar <= 0:
        raise ValueError("Aşama, malzeme ve pozitif miktar zorunludur")
    kayit = db.query(ReceteAsamaMalzeme).filter(ReceteAsamaMalzeme.asama_id == asama.id, ReceteAsamaMalzeme.malzeme_id == malzeme.id).first()
    kayit = kayit or ReceteAsamaMalzeme(asama_id=asama.id, malzeme_id=malzeme.id)
    kayit.miktar, kayit.birim, kayit.fire_orani = miktar, (birim.strip() or malzeme.birim or "Adet")[:20], max(0, fire_orani)
    db.add(kayit); db.commit()
    return kayit


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
    kalemler = db.query(SiparisKalem).filter(SiparisKalem.aktif.is_(True), SiparisKalem.durum != "Tamamlandı").order_by(SiparisKalem.created_at.desc()).all()
    return {"plan_receteleri": receteler, "bekleyen_siparis_kalemleri": kalemler,
        "uretim_planlari": db.query(UretimPlani).filter(UretimPlani.aktif.is_(True)).order_by(UretimPlani.created_at.desc()).limit(50).all(),
        "plan_urun_haritasi": {u.id: u for u in db.query(Urun).all()},
        "plan_siparis_haritasi": {s.id: s for s in db.query(Siparis).all()}}
