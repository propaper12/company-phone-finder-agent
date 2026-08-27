# 📦 Kurulum & Sorun Giderme Rehberi

## 💻 Sistem Gereksinimleri
- **İşletim Sistemi:** Windows 10/11, macOS veya Linux
- **Python:** 3.10 veya daha üstü
- **RAM:** Minimum 2 GB (4 GB önerilir)
- **Disk Alanı:** ~150 MB

---

## 🚀 Windows Kurulumu (1-Tık)

1. Depoyu indirin veya klonlayın:
   ```bash
   git clone https://github.com/propaper12/company-phone-finder-agent.git
   ```
2. Klasör içindeki **`KURULUM_VE_BASLAT.bat`** dosyasına çift tıklayın.
3. Batch betiği:
   - Python'un kurulu olup olmadığını denetler.
   - `requirements.txt` içindeki kütüphaneleri otomatik yükler.
   - Sunucuyu çalıştırır ve tarayıcınızda `http://127.0.0.1:8000` adresini açar.

---

## 🐧 Linux & macOS Kurulumu

```bash
# 1. Depoyu klonlayın
git clone https://github.com/propaper12/company-phone-finder-agent.git
cd company-phone-finder-agent

# 2. Virtual environment oluşturun (Önerilen)
python3 -m venv venv
source venv/bin/activate

# 3. Bağımlılıkları yükleyin
pip install -r requirements.txt

# 4. Sunucuyu başlatın
python3 server.py
```

---

## 🔧 Sık Karşılaşılan Sorunlar & Çözümleri

### 1. `python : The term 'python' is not recognized` Hatası
- **Neden:** Python kurulu değil veya sistem PATH ortam değişkenine eklenmemiş.
- **Çözüm:** [python.org/downloads](https://www.python.org/downloads/) adresinden Python'u kurarken en alttaki **"Add Python to PATH"** kutucuğunu işaretleyin.

### 2. `Port 8000 is already in use` Hatası
- **Neden:** Başka bir program veya önceki bir oturum port 8000'i kullanıyor.
- **Çözüm:** Görev Yöneticisinden `python.exe` sürecini sonlandırın veya `server.py` dosyasında `port=8000` değerini `port=8080` yapın.

### 3. Excel Dosyası Yüklenirken Sütun Algılanamadı
- **Neden:** Dosyanızdaki sütun başlıkları alışılmışın dışında olabilir.
- **Çözüm:** Arayüzün sol panelindeki **"🏢 Şirket Sütunu"** açılır kutusundan şirket unvanlarının bulunduğu sütunu el ile seçebilirsiniz.
