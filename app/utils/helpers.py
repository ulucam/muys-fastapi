"""Genel yardımcı fonksiyonlar.

Uygulamanın farklı katmanlarında tekrar eden küçük dönüşümleri tek
noktada toplar. Buradaki fonksiyonlar saf (pure) olacak şekilde
tasarlanmıştır; veritabanı veya istek bağlamı gerektirmezler.
"""

from datetime import date, datetime


def metin(deger) -> str:
    """Değeri metne çevirir ve baştaki/sondaki boşlukları temizler."""
    return str(deger or "").strip()


def sayi(deger, alan, tam_sayi=False, bos_ta_sifir=False):
    """Değeri sayıya çevirir.

    ``bos_ta_sifir=True`` ise ``None`` ve boş metin 0.0 olarak yorumlanır
    (Excel içe aktarımında boş hücreler için). Aksi halde boş değer
    ``ValueError`` üretir (form doğrulamasında eksik alanı yakalamak için).
    """
    if bos_ta_sifir and deger in (None, ""):
        return 0.0
    try:
        sayisal_deger = float(deger)
        if tam_sayi and not sayisal_deger.is_integer():
            raise ValueError
        return int(sayisal_deger) if tam_sayi else sayisal_deger
    except (TypeError, ValueError):
        raise ValueError(f"{alan} sayısal olmalı")


def kod_uret(kullanilan_kodlar, on_ek: str, basamak: int = 6) -> str:
    """``on_ek`` ile başlayan, sıradaki boştaki kodu üretir.

    Örnek: ``kod_uret({"M000001", "M000003"}, "M")`` → ``"M000002"``.
    """
    en_yuksek_numara = 0
    for kod in kullanilan_kodlar:
        if kod and kod.startswith(on_ek) and kod[len(on_ek):].isdigit():
            en_yuksek_numara = max(en_yuksek_numara, int(kod[len(on_ek):]))

    sira = en_yuksek_numara + 1
    kod = f"{on_ek}{sira:0{basamak}d}"
    while kod in kullanilan_kodlar:
        sira += 1
        kod = f"{on_ek}{sira:0{basamak}d}"
    return kod


def tarih_saat_str(zaman) -> str:
    """``datetime`` değerini ``GG.AA.YYYY SS:DD`` biçiminde döndürür."""
    if zaman is None:
        return ""
    if isinstance(zaman, datetime):
        return zaman.strftime("%d.%m.%Y %H:%M")
    if isinstance(zaman, date):
        return zaman.strftime("%d.%m.%Y")
    return metin(zaman)
