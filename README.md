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
│   │
│   ├── main.py                  # FastAPI başlangıç dosyası
│   ├── database.py              # Engine, SessionLocal, Base, get_db()
│   ├── config.py                # Uygulama ayarları
│   ├── dependencies.py          # Ortak Depends() fonksiyonları
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── musteri.py
│   │   ├── urun.py
│   │   ├── siparis.py           # Siparis + SiparisKalem
│   │   ├── recete.py            # Recete + ReceteDetay
│   │   ├── stok.py              # Stok + StokHareket
│   │   ├── uretim.py
│   │   ├── sevkiyat.py          # Sevkiyat + SevkiyatDetay
│   │   └── makine.py
│   │
│   ├── routers/
│   │   ├── auth.py
│   │   ├── dashboard.py
│   │   ├── musteriler.py
│   │   ├── urunler.py
│   │   ├── siparisler.py
│   │   ├── receteler.py
│   │   ├── uretim.py
│   │   ├── stok.py
│   │   └── sevkiyat.py
│   │
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── siparis_service.py
│   │   ├── stok_service.py
│   │   ├── uretim_service.py
│   │   ├── recete_service.py
│   │   └── sevkiyat_service.py
│   │
│   ├── schemas/
│   │   ├── user.py
│   │   ├── musteri.py
│   │   ├── urun.py
│   │   ├── siparis.py
│   │   ├── recete.py
│   │   ├── stok.py
│   │   └── sevkiyat.py
│   │
│   ├── templates/
│   │   ├── base.html
│   │   ├── auth/
│   │   ├── dashboard/
│   │   ├── musteriler/
│   │   ├── urunler/
│   │   ├── siparisler/
│   │   ├── receteler/
│   │   ├── uretim/
│   │   ├── stok/
│   │   └── sevkiyat/
│   │
│   ├── static/
│   │   ├── css/
│   │   ├── js/
│   │   ├── img/
│   │   └── icons/
│   │
│   └── utils/
│       ├── excel.py
│       ├── barcode.py
│       ├── pdf.py
│       └── helpers.py
│
├── .env
├── .gitignore
├── requirements.txt
├── README.md
└── run.py
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

* get_db()
* get_current_user()
* admin kontrolü

---

## models/

SQLAlchemy tabloları burada bulunur.

Her dosya yalnızca kendi tablolarını içerir.

Örnek:

siparis.py

* Siparis
* SiparisKalem

---

## routers/

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

## schemas/

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

* Excel işlemleri
* PDF oluşturma
* Barkod oluşturma
* Genel yardımcı fonksiyonlar

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
