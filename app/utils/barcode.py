"""Barkod yardımcı fonksiyonları.

EAN-13 (GTIN-13) standardına uygun barkod kontrol rakamı hesaplama ve
doğrulama. Ürün kartlarındaki barkod alanının tutarlılığını sağlamak
için kullanılır; bağımlılık gerektirmez.
"""

from app.utils.helpers import metin


def ean13_kontrol_rakami(ilk_12_hane: str) -> int:
    """EAN-13 için 13. (kontrol) rakamı hesaplar.

    İlk 12 hane verildiğinde standart algoritma ile kontrol rakamı
    döndürülür. Girdi 12 haneli sayısal bir metin olmalıdır.
    """
    hane = metin(ilk_12_hane)
    if len(hane) != 12 or not hane.isdigit():
        raise ValueError("Barkod 12 haneli sayısal bir değer olmalı")
    toplam = sum(int(h) * (1 if i % 2 == 0 else 3) for i, h in enumerate(hane))
    return (10 - toplam % 10) % 10


def ean13_dogrula(barkod: str) -> bool:
    """13 haneli bir barkodun kontrol rakamını doğrular."""
    hane = metin(barkod)
    if len(hane) != 13 or not hane.isdigit():
        return False
    return ean13_kontrol_rakami(hane[:12]) == int(hane[12])


def barkod_uret(ilk_12_hane: str) -> str:
    """12 haneli ürün kodundan tam EAN-13 barkod metni üretir."""
    return metin(ilk_12_hane) + str(ean13_kontrol_rakami(ilk_12_hane))
