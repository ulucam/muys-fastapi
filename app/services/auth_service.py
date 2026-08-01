from passlib.context import CryptContext

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


def sifre_hashle(sifre: str):
    return pwd_context.hash(sifre)


def sifre_dogrula(duz_sifre: str, hashli_sifre: str):
    return pwd_context.verify(
        duz_sifre,
        hashli_sifre
    )
