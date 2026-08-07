# MÜYS - Üretim Yönetim Sistemi

## Proje Amacı

MÜYS, üretim yapan işletmeler için geliştirilen web tabanlı bir üretim yönetim sistemidir.

Sistemin temel amacı;

* Müşteri yönetimi
* Ürün yönetimi
* Ürün reçeteleri
* Sipariş takibi
* Üretim takibi
* Stok yönetimi
* Sevkiyat yönetimi

işlemlerini tek bir sistem üzerinden yönetmektir.

---

# Proje Klasör Yapısı

```text
MUYS/
│
├── app/
│   ├── main.py                  # FastAPI başlangıç dosyası
│   ├── database.py              # Engine, SessionLocal, Base, get_db()
│   ├── config.py                # Uygulama ayarları (.env)
│   ├── dependencies.py          # Ortak Depends() fonksiyonları (yetki kontrolü)
│   ├── templating.py            # Paylaşılan Jinja2 şablon motoru
│   ├── password.py              # pwdlib/Argon2 parola hashleme
│   ├── product_types.py         # Ürün türü sözlüğü ve normalizasyonu
│   ├── migrations.py            # Geriye uyumlu ALTER TABLE migrationları
│   ├── startup.py               # Uygulama açılış hazırlıkları
│   ├── setup.py                 # Varsayılan rol/admin/veri kurulumu
│   │
│   ├── models/                  # SQLAlchemy tabloları (her dosya kendi tabloları)
│   ├── routes/                  # Sayfa ve API endpointleri
│   ├── services/                # İş kuralları (SQL burada yazılır)
│   ├── schemas.py               # Pydantic modelleri
│   ├── excel/                   # Excel içe aktarım yardımcıları
│   ├── utils/                   # Yardımcı fonksiyonlar
│   │   ├── excel.py             # Excel şablon/aktarım işlemleri
│   │   ├── barcode.py           # EAN-13 barkod kontrol rakamı
│   │   ├── pdf.py               # Bağımlılıksız metin PDF üretici
│   │   ├── helpers.py           # Genel yardımcılar (metin, sayı, kod)
│   │   ├── zaman.py             # Türkiye saati dönüşümleri
│   │   └── uretim_excel.py      # Üretim Excel okuma/şablon
│   │
│   ├── templates/               # HTML şablonları (Jinja2)
│   └── static/                  # CSS, JS, resim, ikon
│
├── scripts/
│   └── generate_vapid_keys.py   # Web Push VAPID anahtar üretici
├── tests/                       # Pytest testleri
├── .env.example
├── .gitignore
├── requirements.txt
├── pyproject.toml
└── render.yaml
```

---

# Klasörlerin Görevleri

## app/

Uygulamanın ana klasörüdür.

Tüm kaynak kodlar burada bulunur.

---

## main.py

Uygulamanın giriş noktasıdır.

Görevleri:

* FastAPI uygulamasını oluşturmak
* Router'ları sisteme eklemek
* Middleware tanımlamak
* Uygulamayı başlatmak

Bu dosyada iş mantığı yazılmaz.

---

## database.py

Veritabanı bağlantısını yönetir.

İçerisinde;

* Engine
* SessionLocal
* Base
* get_db()

bulunur.

---

## config.py

Uygulamanın ayarlarını yönetir.

Örnek:

* DATABASE_URL
* SECRET_KEY
* DEBUG
* Upload klasörleri

---

## dependencies.py

Ortak kullanılan Depends() fonksiyonları burada bulunur.

Örnek:

* `yetki_kontrol(izinli_roller)` — rol bazlı erişim denetimi
* `kullanici_yonetim_kontrol` — kullanıcı yönetimi yetki denetimi

`app/security.py` geriye uyumluluk için bu fonksiyonları yeniden dışa aktarır.

---

## models/

SQLAlchemy tabloları burada bulunur.

Her dosya yalnızca kendi tablolarını içerir.

Örnek:

siparis.py

* Siparis
* SiparisKalem

---

## routes/

Sayfaları ve API endpointlerini yönetir.

Görevleri:

* HTTP isteklerini almak
* Service katmanını çağırmak
* HTML veya JSON döndürmek

---

## services/

Programın tüm iş kuralları burada bulunur.

Örnek:

* Sipariş oluştur
* Stok düş
* Üretim kaydet
* Sevkiyat oluştur

Programın asıl beyni burasıdır.

---

## schemas.py

Pydantic modelleridir.

API veri doğrulaması burada yapılır.

---

## templates/

HTML dosyaları burada bulunur.

Her modül kendi klasörüne sahiptir.

---

## static/

Statik dosyalar.

* CSS
* JavaScript
* Resimler
* İkonlar

---

## utils/

Yardımcı fonksiyonlar.

Örnek:

* Excel işlemleri (`excel.py`)
* Barkod oluşturma (`barcode.py` — EAN-13)
* PDF oluşturma (`pdf.py`)
* Genel yardımcı fonksiyonlar (`helpers.py`)
* Türkiye saati dönüşümleri (`zaman.py`)

---

# Proje Kuralları

## Kural 1

Router içinde SQL sorgusu yazılmaz.

Yanlış:

Router

↓

SQL

Doğru:

Router

↓

Service

↓

Database

---

## Kural 2

Service katmanı HTML bilmez.

Service yalnızca iş mantığını yönetir.

HTML yalnızca Router tarafından döndürülür.

---

## Kural 3

Model dosyaları sadece tablo tanımlar.

Model içerisinde;

* HTML
* API
* İş mantığı

bulunmaz.

Sadece SQLAlchemy modelleri yer alır.

---

# Geliştirme Prensipleri

* Kod okunabilir olacak.
* Modüller birbirinden bağımsız olacak.
* Gereksiz tekrar yapılmayacak.
* Her yeni özellik mevcut mimariye uygun geliştirilecek.
* Kod kısa değil, sürdürülebilir olacak.
* Performans kadar bakım kolaylığı da öncelikli olacak.

---

# MÜYS Felsefesi

MÜYS yalnızca bir stok veya sipariş programı değildir.

Amaç;

üretimden sevkiyata kadar tüm süreci tek merkezden yönetebilen, ileride makine ve tablet entegrasyonuna açık, modüler ve uzun yıllar geliştirilebilecek profesyonel bir üretim yönetim sistemi oluşturmaktır.

---

# Web Push Kurulumu

Uygulama PWA ve Web Push desteğine sahiptir. Cihaz bildirimlerini etkinleştirmek için:

1. Bağımlılıkları kurun: `pip install -r requirements.txt`
2. Anahtarları bir kez üretin: `python scripts/generate_vapid_keys.py`
3. Çıktıdaki `VAPID_PUBLIC_KEY`, `VAPID_PRIVATE_KEY` ve `VAPID_SUBJECT` değerlerini `.env` veya Render ortam değişkenlerine ekleyin.
4. Uygulamayı HTTPS üzerinden yayınlayın.
5. Kullanıcı navbar bildirim menüsündeki **Bildirimleri Aç** düğmesine basarak cihazını kaydeder.

VAPID anahtarları sabit tutulmalıdır. Anahtarlar değiştirilirse mevcut cihazların yeniden abone olması gerekir. `VAPID_PRIVATE_KEY` repoya eklenmez.

Render Blueprint dosyası bu üç değeri `sync: false` olarak tanımlar. Render Dashboard'da servis için **Environment** bölümüne gidip üretilen değerleri bir kez kaydedin ve servisi yeniden deploy edin. Otomatik veritabanı anahtarı yalnızca ortam değişkenleri bulunmadığında yedek olarak kullanılır.

---

# Testler

Testler `pytest` ile çalıştırılır:

```bash
pip install -r requirements.txt
pip install pytest
pytest
```

Testler bellek içi SQLite kullanır; harici veritabanı veya donanım gerektirmez.
