from sqlalchemy.orm import Session

from app.models.user import User
from app.password import sifre_olustur


def admin_olustur(db: Session):

    admin = (
        db.query(User)
        .filter(User.rol == "Admin")
        .first()
    )

    if admin:
        return

    admin = User(
        kullanici_adi="admin",
        ad_soyad="Sistem Yöneticisi",
        sifre=sifre_olustur("admin123"),
        rol="Admin",
        aktif=True
    )

    db.add(admin)
    db.commit()

    print("✅ Varsayılan admin oluşturuldu.")