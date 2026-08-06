from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine


def uyumluluk_migrationlarini_uygula(engine: Engine) -> None:
    """Eski kurulumlarda bulunmayan sütunları geriye uyumlu biçimde ekler."""
    with engine.begin() as connection:
        denetleyici = inspect(connection)
        migrationlar = {
            "musteriler": [
                ("musteri_turu", "ALTER TABLE musteriler ADD COLUMN musteri_turu VARCHAR(30) NOT NULL DEFAULT 'Alıcı'"),
            ],
            "urunler": [
                ("urun_sinifi_id", "ALTER TABLE urunler ADD COLUMN urun_sinifi_id INTEGER"),
                ("urun_cinsi", "ALTER TABLE urunler ADD COLUMN urun_cinsi VARCHAR(100)"),
            ],
            "recete_kalemleri": [
                ("hedef_cevrim_suresi", "ALTER TABLE recete_kalemleri ADD COLUMN hedef_cevrim_suresi FLOAT DEFAULT 0"),
            ],
            "kullanicilar": [
                ("istasyon_id", "ALTER TABLE kullanicilar ADD COLUMN istasyon_id INTEGER REFERENCES istasyonlar(id)"),
                ("personel_id", "ALTER TABLE kullanicilar ADD COLUMN personel_id INTEGER REFERENCES personeller(id)"),
            ],
            "firma_ayarlari": [
                ("logo_yolu", "ALTER TABLE firma_ayarlari ADD COLUMN logo_yolu VARCHAR(300) DEFAULT ''"),
            ],
        }
        for tablo, sutun_migrationlari in migrationlar.items():
            mevcut_sutunlar = {sutun["name"] for sutun in denetleyici.get_columns(tablo)}
            for sutun_adi, sql in sutun_migrationlari:
                if sutun_adi not in mevcut_sutunlar:
                    connection.execute(text(sql))

        if "firma_ayarlari" in denetleyici.get_table_names():
            firma_sutunlari = {sutun["name"] for sutun in denetleyici.get_columns("firma_ayarlari")}
            ikili_tur = "BYTEA" if engine.dialect.name == "postgresql" else "BLOB"
            if "logo_verisi" not in firma_sutunlari:
                connection.execute(text(f"ALTER TABLE firma_ayarlari ADD COLUMN logo_verisi {ikili_tur}"))
            if "logo_mime_turu" not in firma_sutunlari:
                connection.execute(text("ALTER TABLE firma_ayarlari ADD COLUMN logo_mime_turu VARCHAR(100) DEFAULT ''"))

        # Eski operatörlerin tekil istasyon bilgisini yeni çoklu ilişki tablosuna taşır.
        tablolar = set(denetleyici.get_table_names())
        if {"kullanicilar", "personel_istasyon_atamalari"}.issubset(tablolar):
            connection.execute(text("""
                INSERT INTO personel_istasyon_atamalari (personel_id, istasyon_id, aktif, created_at, updated_at)
                SELECT k.personel_id, k.istasyon_id, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                FROM kullanicilar k
                WHERE k.personel_id IS NOT NULL AND k.istasyon_id IS NOT NULL
                  AND NOT EXISTS (
                    SELECT 1 FROM personel_istasyon_atamalari pi
                    WHERE pi.personel_id = k.personel_id AND pi.istasyon_id = k.istasyon_id
                  )
            """))
