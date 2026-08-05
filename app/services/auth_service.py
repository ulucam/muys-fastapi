from sqlalchemy.orm import Session

from app.models.user import User
from app.password import sifre_kontrol, sifre_olustur


def sifre_hashle(sifre: str) -> str:
    """Parolayı uygulamanın aktif parola sağlayıcısıyla hashler."""
    return sifre_olustur(sifre)


def sifre_dogrula(duz_sifre: str, hashli_sifre: str) -> bool:
    """Girilen parola ile kayıtlı parola hashini karşılaştırır."""
    return sifre_kontrol(duz_sifre, hashli_sifre)


def kullanici_dogrula(
    db: Session,
    kullanici_adi: str | None,
    sifre: str | None,
) -> User | None:
    """Kimlik bilgileri doğruysa kullanıcıyı, değilse ``None`` döndürür."""
    if not kullanici_adi or not sifre:
        return None

    kullanici = (
        db.query(User)
        .filter(User.kullanici_adi == kullanici_adi)
        .first()
    )

    if not kullanici or not sifre_dogrula(sifre, kullanici.sifre):
        return None

    return kullanici
