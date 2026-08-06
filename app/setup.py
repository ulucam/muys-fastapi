from sqlalchemy.orm import Session

from app.models.user import User
from app.password import sifre_olustur
from app.models.stok_urun_turu import StokUrunTuru


def setup_database(db: Session):

    try:

        for ad, uretilen in [("Hammadde", False), ("Sarf Malzeme", False), ("Üretim", True), ("Ticari Mamül", False)]:
            if not db.query(StokUrunTuru).filter(StokUrunTuru.adi == ad).first():
                db.add(StokUrunTuru(adi=ad, uretilen=uretilen, aktif=True))
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
