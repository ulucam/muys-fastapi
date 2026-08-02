from sqlalchemy.orm import Session

from app.models.user import User
from app.password import sifre_olustur


def setup_database(db: Session):

    admin = (
        db.query(User)
        .filter(User.kullanici_adi == "admin")
        .first()
    )

    if admin:

        admin.sifre = sifre_olustur("admin123")
        admin.ad_soyad = "Sistem Yöneticisi"
        admin.email = "admin@muys.local"
        admin.rol = "Admin"
        admin.aktif = True

        db.commit()

        print("✅ Admin güncellendi.")

    else:

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

        db.commit()

        print("✅ Varsayılan admin oluşturuldu.")