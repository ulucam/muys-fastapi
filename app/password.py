from passlib.context import CryptContext


pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


def sifre_olustur(sifre: str):

    return pwd_context.hash(sifre)



def sifre_kontrol(
    girilen_sifre: str,
    kayitli_sifre: str
):

    return pwd_context.verify(
        girilen_sifre,
        kayitli_sifre
    )