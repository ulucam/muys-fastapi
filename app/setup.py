from sqlalchemy.orm import Session

from app.models.user import User
from app.password import sifre_olustur
from app.models.stok_urun_turu import StokUrunTuru
from app.models.rol_sinifi import RolSinifi


def setup_database(db: Session):

    try:

        for ad, uretilen in [("Hammadde", False), ("Sarf Malzeme", False), ("Üretim", True), ("Ticari Mamül", False)]:
            if not db.query(StokUrunTuru).filter(StokUrunTuru.adi == ad).first():
                db.add(StokUrunTuru(adi=ad, uretilen=uretilen, aktif=True))
        db.commit()

        varsayilan_roller = [
            ("Admin", 100, True, "Tüm modüller", True),
            ("Patron", 90, False, "Onay ve izleme", True),
            ("Yönetici", 80, False, "Yönetim ekranları", True),
            ("Üretim", 60, False, "Üretim ve reçete", True),
            ("Satış", 50, False, "Müşteri ve sipariş", True),
            ("Depo", 40, False, "Stok işlemleri", True),
            ("Operatör", 20, False, "Atandığı istasyonlar", True),
        ]
        for ad, seviye, ekleyebilir, yetkiler, sistem_rolu in varsayilan_roller:
            if not db.query(RolSinifi).filter(RolSinifi.adi == ad).first():
                db.add(RolSinifi(adi=ad, seviye=seviye, kullanici_ekleyebilir=ekleyebilir,
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

    except Exception as e:

        db.rollback()

        print(f"❌ Setup hatası: {e}")

        raise
