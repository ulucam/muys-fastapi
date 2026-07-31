# MÜYS - Üretim Yönetim Sistemi

FastAPI ile geliştirilmiş üretim yönetim sistemi.

## API Endpoints

- `GET /` - Ana sayfa
- `GET /api/health` - Sağlık kontrolü

## Kurulum

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload

---

## 🔗 ADIM 2: GitHub'a Yükle

### 1️⃣ GitHub'da Yeni Repo Oluştur

1. [github.com](https://github.com) git
2. **"New repository"** tıkla
3. Adı: `muys-fastapi`
4. **"Create repository"** tıkla

### 2️⃣ Dosyaları Yükle

**"Add file"** → **"Upload files"** ile tüm dosyaları sürükle-bırak yap veya tek tek oluştur.

---

## 🌐 ADIM 3: Render'da Deploy Et

### 1️⃣ Render'da Yeni Web Service

1. [dashboard.render.com](https://dashboard.render.com) git
2. **"New +"** → **"Web Service"**
3. **"Connect GitHub"** → `muys-fastapi` repo'sunu seç

### 2️⃣ Ayarları Yap

| Alan | Değer |
|------|-------|
| Name | `muys-fastapi` |
| Environment | `Python 3` |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `uvicorn app.main:app --host 0.0.0.0 --port 10000` |

### 3️⃣ **"Create Web Service"** Tıkla

---

## ✅ ADIM 4: Test Et

**Ana Sayfa:**
