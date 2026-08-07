"""PDF yardımcı fonksiyonları.

Harici bağımlılık gerektirmeden tek sayfalık metin tabanlı PDF
üretir. Sevkiyat irsaliyesi, sipariş teyidi gibi yazdırma
ihtiyaçları için yeterlidir; görsel zenginliği yüksek belgeler
için harici bir kütüphane önerilir.
"""

from datetime import date, datetime


def _pdf_metni_kaçir(metin: str) -> str:
    """PDF metin operatörleri için özel karakterleri kaçırır."""
    return (
        metin.replace("\\", "\\\\")
        .replace("(", "\\(")
        .replace(")", "\\)")
        .replace("\n", " ")
    )


def _tarih_metni(zaman) -> str:
    if isinstance(zaman, datetime):
        return zaman.strftime("%d.%m.%Y %H:%M")
    if isinstance(zaman, date):
        return zaman.strftime("%d.%m.%Y")
    return str(zaman or "")


def metin_pdf_uret(satirlar: list[str], baslik: str = "", tarih=None, alt_bilgi: str = "") -> bytes:
    """Satır listesinden tek sayfalık A4 PDF üretir.

    - ``satirlar``: belge gövdesindeki metin satırları
    - ``baslik``: sayfa üstündeki başlık (opsiyonel)
    - ``tarih``: sağ üstte gösterilen tarih (opsiyonel)
    - ``alt_bilgi``: sayfa altındaki bilgi satırı (opsiyonel)
    """
    sayfa_genisligi = 595.0
    satir_yuksekligi = 14.0
    ust_kenar = 60.0
    alt_kenar = 60.0
    metin_satirlari: list[str] = []

    # İçerik akışı (Content stream) oluştur
    akis: list[str] = ["BT", "/F1 11 Tf", f"1 0 0 1 50 {sayfa_genisligi - ust_kenar} Tm", "16 TL"]
    if baslik:
        akis.append(f"/F1 14 Tf")
        akis.append(f"({_pdf_metni_kaçir(baslik)}) Tj")
        akis.append("0 -20 Td")
        akis.append("/F1 11 Tf")
    if tarih:
        akis.append(f"/F1 9 Tf")
        akis.append(f"({_pdf_metni_kaçir(_tarih_metni(tarih))}) Tj")
        akis.append("0 -16 Td")
        akis.append("/F1 11 Tf")
    for satir in satirlar:
        akis.append(f"({_pdf_metni_kaçir(satir)}) Tj")
        akis.append("T*")
    if alt_bilgi:
        akis.append("0 12 Td")
        akis.append("/F1 9 Tf")
        akis.append(f"({_pdf_metni_kaçir(alt_bilgi)}) Tj")
    akis.append("ET")
    icerik = "\n".join(akis).encode("latin-1", "replace")

    # PDF nesneleri
    nesneler = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
            b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>"
        ),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(icerik)).encode() + b" >>\nstream\n" + icerik + b"\nendstream",
    ]

    cikti = bytearray(b"%PDF-1.4\n")
    ofsetler = []
    for i, nesne in enumerate(nesneler, start=1):
        ofsetler.append(len(cikti))
        cikti += f"{i} 0 obj\n".encode() + nesne + b"\nendobj\n"

    xref_baslangici = len(cikti)
    cikti += f"xref\n0 {len(nesneler) + 1}\n".encode()
    cikti += b"0000000000 65535 f \n"
    for ofset in ofsetler:
        cikti += f"{ofset:010d} 00000 n \n".encode()
    cikti += (
        f"trailer\n<< /Size {len(nesneler) + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref_baslangici}\n%%EOF\n"
    ).encode()
    return bytes(cikti)
