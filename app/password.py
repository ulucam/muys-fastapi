from pwdlib import PasswordHash

password_hash = PasswordHash.recommended()


def sifre_olustur(sifre: str):
    return password_hash.hash(sifre)


def sifre_kontrol(girilen_sifre: str, kayitli_sifre: str):
    return password_hash.verify(girilen_sifre, kayitli_sifre)