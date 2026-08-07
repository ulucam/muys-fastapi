"""Ürün kartlarında kullanılan ortak tür sözlüğü."""

URUN_TURLERI = (
    "Hammadde",
    "Mamül",
    "Sarf Malzeme",
    "Ticari Mamül",
    "Üretim",
    "Yarı Mamül",
)


def urun_turunu_normalize_et(deger: object) -> str:
    """Eski yazımları tek ekranda kullanılan değerlerle eşler.

    Sözlükte olmayan bir değer bilinçli olarak boş döner; böylece kullanıcı
    karttan doğru türü seçer ve eski serbest metinler sistem davranışını
    değiştirmez.
    """
    donusum = str.maketrans({"ı": "i", "İ": "i", "ş": "s", "ğ": "g", "ü": "u", "ö": "o", "ç": "c"})
    anahtar = "".join(harf for harf in str(deger or "").casefold().translate(donusum) if harf.isalnum())
    eslesmeler = {
        "hammadde": "Hammadde",
        "mamul": "Mamül",
        "sarfmalzeme": "Sarf Malzeme",
        "ticarimamul": "Ticari Mamül",
        "uretim": "Üretim",
        "yarimamul": "Yarı Mamül",
    }
    return eslesmeler.get(anahtar, "")
