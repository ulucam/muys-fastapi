from app.database import SessionLocal
from app.models.user import User

db = SessionLocal()

kontrol = db.query(User).filter(
    User.kullanici_adi == "admin"
).first()

if kontrol:
    print("Admin zaten mevcut.")
else:
    admin = User(
        kullanici_adi="admin",
        sifre="123456",
        ad_soyad="Sistem Yöneticisi",
        email="admin@muys.com",
        telefon="",
        rol="Admin",
        aktif=True
    )

    db.add(admin)
    db.commit()

    print("Admin oluşturuldu.")