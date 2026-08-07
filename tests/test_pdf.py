"""app.utils.pdf birim testleri."""

import re

from app.utils.pdf import metin_pdf_uret


class TestMetinPdfUret:
    def test_pdf_basligi(self):
        pdf = metin_pdf_uret(["a"], baslik="Test")
        assert pdf.startswith(b"%PDF-1.4")

    def test_pdf_sonu(self):
        pdf = metin_pdf_uret(["a"])
        assert pdf.rstrip().endswith(b"%%EOF")

    def test_icerik_satirlari(self):
        pdf = metin_pdf_uret(["satir-bir", "satir-iki"], baslik="baslik-metni")
        assert b"satir-bir" in pdf
        assert b"satir-iki" in pdf
        assert b"baslik-metni" in pdf

    def test_xref_ve_trailer(self):
        pdf = metin_pdf_uret(["x"])
        assert b"xref" in pdf
        assert b"trailer" in pdf
        assert b"/Type /Page" in pdf

    def test_ozel_karakter_kaçis(self):
        pdf = metin_pdf_uret(["parantez (test) ve slash \\ test"])
        assert b"parantez" in pdf

    def test_tarih(self):
        pdf = metin_pdf_uret(["a"], tarih="07.08.2026")
        assert b"07.08.2026" in pdf
