from sqlalchemy.orm import Session

from app.models.user import User
from app.password import sifre_olustur
from app.models.stok_urun_turu import StokUrunTuru
from app.models.rol_sinifi import RolSinifi
from app.models.mesaj_konusu import MesajKonusu, MesajKonusuYetkili


def setup_database(db: Session):

    try:

        # Varsayılan stok türleri yalnızca ilk, tamamen boş kurulumda eklenir.
        # Kullanıcının sildiği veya yeniden adlandırdığı türler açılışta geri gelmemelidir.
        if db.query(StokUrunTuru).count() == 0:
            for ad, uretilen in [("Hammadde", False), ("Sarf Malzeme", False), ("Üretim", True), ("Ticari Mamül", False)]:
                db.add(StokUrunTuru(adi=ad, uretilen=uretilen, aktif=True))
        db.commit()

        varsayilan_roller = [
            ("Admin", 100, True, True, True, "Tüm modüller", True),
            ("Patron", 90, False, False, False, "Onay ve izleme", True),
            ("Yönetici", 80, False, False, False, "Yönetim ekranları", True),
            ("Üretim", 60, False, False, False, "Üretim ve reçete", True),
            ("Satış", 50, False, False, False, "Müşteri ve sipariş", True),
            ("Depo", 40, False, False, False, "Stok işlemleri", True),
            ("Operatör", 20, False, False, False, "Atandığı istasyonlar", True),
        ]
        for ad, seviye, ekleyebilir, yedekleme_yapabilir, loglarini_gorebilir, yetkiler, sistem_rolu in varsayilan_roller:
            if not db.query(RolSinifi).filter(RolSinifi.adi == ad).first():
                db.add(RolSinifi(adi=ad, seviye=seviye, kullanici_ekleyebilir=ekleyebilir,
                    yedekleme_yapabilir=yedekleme_yapabilir, loglarini_gorebilir=loglarini_gorebilir,
                    yetkiler=yetkiler, sistem_rolu=sistem_rolu, aktif=True))
        db.commit()

        admin = (
            db.query(User)
            .filter(User.kullanici_adi == "admin")
            .first()
        )

        if not admin:

            admin = User(

                kullanici_adi="admin",

                sifre=sifre_olustur("admin123"),

                ad_soyad="Sistem Yöneticisi",

                email="admin@muys.local",

                telefon="",

                rol="Admin",

                aktif=True

            )

            db.add(admin)

            print("✅ Varsayılan admin oluşturuldu.")
            db.commit()
        else:
            print("✅ Admin hesabı mevcut; değiştirilmedi.")

        varsayilan_konular = [("Genel", "primary"), ("Sipariş", "info"), ("Stok", "warning"), ("Üretim", "success"), ("Acil", "danger")]
        for ad, renk in varsayilan_konular:
            konu = db.query(MesajKonusu).filter(MesajKonusu.adi == ad).first()
            if not konu:
                konu = MesajKonusu(adi=ad, renk=renk, aktif=True)
                db.add(konu); db.flush()
            if not db.query(MesajKonusuYetkili).filter(MesajKonusuYetkili.konu_id == konu.id, MesajKonusuYetkili.kullanici_id == admin.id).first():
                db.add(MesajKonusuYetkili(konu_id=konu.id, kullanici_id=admin.id))
        db.commit()

    except Exception as e:

        db.rollback()

        print(f"❌ Setup hatası: {e}")

        raise
