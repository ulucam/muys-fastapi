import pandas as pd
from sqlalchemy.orm import Session
from app.models.musteri import Musteri

def import_musteriler_from_excel(db: Session, file_contents: bytes):
    """
    Excel dosyasından müşteri verilerini okur ve veritabanına ekler.
    """
    # Excel dosyasını veri çerçevesine alıyoruz
    df = pd.read_excel(file_contents)
    
    # Kolon isimlerini küçük harfe çevirip boşlukları temizleyelim
    df.columns = [str(col).strip().lower() for col in df.columns]
    
    eklenen_sayisi = 0
    guncellenen_sayisi = 0

    for _, row in df.iterrows():
        kod = str(row.get("kod", "")).strip() if pd.notna(row.get("kod")) else None
        unvan = str(row.get("unvan", "")).strip() if pd.notna(row.get("unvan")) else None

        if not unvan:
            continue  # Unvan yoksa bu satırı atla

        # Müşteri koda veya unvana göre var mı kontrol et
        musteri = None
        if kod:
            musteri = db.query(Musteri).filter(Musteri.kod == kod).first()
        if not musteri and unvan:
            musteri = db.query(Musteri).filter(Musteri.unvan == unvan).first()

        if not musteri:
            musteri = Musteri()
            db.add(musteri)
            eklenen_sayisi += 1
        else:
            guncellenen_sayisi += 1

        # Alanları güncelle
        musteri.kod = kod
        musteri.unvan = unvan
        musteri.vergi_dairesi = str(row.get("vergi dairesi", "")).strip() if pd.notna(row.get("vergi dairesi")) else None
        musteri.vergi_no = str(row.get("vergi no", "")).strip() if pd.notna(row.get("vergi no")) else None
        musteri.telefon = str(row.get("telefon", "")).strip() if pd.notna(row.get("telefon")) else None
        musteri.e_posta = str(row.get("e-posta", "")).strip() if pd.notna(row.get("e-posta")) else None
        musteri.il = str(row.get("il", "")).strip() if pd.notna(row.get("il")) else None
        musteri.ilce = str(row.get("ilçe", "")).strip() if pd.notna(row.get("ilçe")) else None
        musteri.adres = str(row.get("adres", "")).strip() if pd.notna(row.get("adres")) else None

    db.commit()
    return {"eklenen": eklenen_sayisi, "guncellenen": guncellenen_sayisi}
