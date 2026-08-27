# ⚡ 10K Şirket Telefon & AI İstihbarat Agent

<div align="center">

![License](https://img.shields.io/badge/License-MIT-blue.svg)
![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-18%2B-61DAFB.svg?logo=react&logoColor=black)
![TypeScript](https://img.shields.io/badge/TypeScript-5.0%2B-3178C6.svg?logo=typescript&logoColor=white)
![Privacy](https://img.shields.io/badge/Privacy-100%25%20Local-success.svg)

**Türkiye'deki on binlerce şirketin yer aldığı dev Excel listelerini tarayarak doğrulanmış kurumsal telefon numaralarını en yüksek doğruluk ve hızla bulan otonom yapay zeka istihbarat motoru.**

[Kurulum Rehberi](#-hızlı-kurulum-1-dakika) • [Özellikler](#-öne-çıkan-özellikler) • [Mimari](#-teknik-mimari) • [Dokümantasyon](docs/)

</div>

---

## 🌟 Öne Çıkan Özellikler

- 🚀 **4 Kademeli Derin Arama Motoru:**
  1. *Firma Rehberleri:* `Find.com.tr`, `Firmatlas`, `Bulurum.com` doğrulanmış dizin önbelleği.
  2. *Lokasyon & İlçe Filtresi:* 81 ilin resmi alan kodlarıyla adaş şirketleri eleyen çapraz coğrafi doğrulama.
  3. *Resmi Web Sitesi Keşfi:* Şirketlerin ana sayfa ve `/iletisim`, `/bize-ulasin` sayfalarından regex ve schema ile tel ayıklama.
  4. *Yetkili & Şahıs Eşleştirmesi:* Küçük işletmelerde şirket sahibi / unvan kombinasyonundan numara tespiti.
- 🔍 **Find.com.tr Dahili Arama & 1-Tıkla Numara Girişi:**
  - Bulunamayan şirketleri doğrudan Find.com.tr sayfasına yönlendiren ve bulunan numarayı tek tıkla Excel'e işleyen akıllı modal.
- ⚠️ **"Neden Bulunamadı?" Akıllı Teşhis Raporu:**
  - Askıda/tasfiyede olan, web sitesinde sadece form bulunan veya adaş şirket elemesi yapılan satırların teşhisini açıklar.
- ⚛️ **Modern React 2026 SaaS Arayüzü:**
  - 60 FPS akıcılıkta Bento-Grid dashboard, canlı radar, anlık hız sayacı ve donmayan sanal tablo.
- 📊 **İnteraktif Excel Grid:**
  - Numarası olanlar en üstte, canlı hücre düzenleme, tek tıkla telefon kopyalama (`📋`) ve anında `.xlsx` kaydı.
- 🛡️ **Otomatik Kayıt (Checkpoint):**
  - Her 15 satırda bir diske otomatik kayıt. Elektrik veya bağlantı kesilse bile veri kaybı yaşanmaz.
- 🔒 **%100 Yerel ve Gizli:**
  - Excel verileriniz asla dış sunuculara veya buluta aktarılmaz, tüm işlemler yerel makinenizde çalışır.

---

## 🚀 Hızlı Kurulum (1 Dakika)

### Yöntem 1: Tek Tıkla Başlatıcı (Windows)
Klasör içindeki **`KURULUM_VE_BASLAT.bat`** dosyasına çift tıklayın. 
Gerekli tüm kütüphaneler otomatik kurulur ve tarayıcınızda `http://127.0.0.1:8000` açılır.

### Yöntem 2: Manuel Kurulum (Tüm İşletim Sistemleri)

```bash
# 1. Depoyu klonlayın
git clone https://github.com/propaper12/company-phone-finder-agent.git
cd company-phone-finder-agent

# 2. Python bağımlılıklarını kurun
pip install -r requirements.txt

# 3. Sunucuyu başlatın
python server.py
```

Tarayıcınızda **`http://127.0.0.1:8000`** adresine gidin.

---

## 📖 Kullanım Kılavuzu

```
1. 📂 Excel/CSV Dosyası Seçin  ➔  
2. ⚙️ Worker Hızını Ayarlayın   ➔  (Maksimum hız için 20 - 25 Worker)
3. 🚀 Taramayı Başlatın         ➔  (Canlı Radardan ilerlemeyi izleyin)
4. 🔍 Find.com.tr Entegrasyonu ➔  (Bulunamayanları 1-tıkla açın ve numarayı kaydedin)
5. 📥 Sonuçları İndirin        ➔  (Numaraları ve Teşhis sütunları eklenmiş Excel)
```

---

## 🏗️ Proje Yapısı

```
├── KURULUM_VE_BASLAT.bat   # Windows 1-tıkla otomatik kurucu ve başlatıcı
├── baslat.bat              # Hızlı başlatıcı
├── server.py               # FastAPI Backend & WebSocket Sunucusu
├── search_engine.py        # 4 Kademeli Türkçe Şirket Arama & Teşhis Motoru
├── find_service.py         # Find.com.tr Hızlı Köprü & Arama Servisi
├── excel_manager.py        # Excel/CSV Okuma, Yazma, Sütun Tespiti & Checkpoint
├── extractor.py            # Telefon Regex & Doğrulama Motoru
├── name_cleaner.py         # Şirket Unvanı Temizleme (A.Ş., Ltd. Şti. filtreleme)
├── city_codes.py           # 81 İl Alan Kodu Sözlüğü
├── ai_analyst.py           # Yerel AI Şirket İstihbarat Analisti
├── requirements.txt        # Python Bağımlılıkları
├── docs/                   # Detaylı Teknik Dokümantasyon
│   ├── ARCHITECTURE.md     # Sistem Mimarisi & Arama Akışı
│   ├── INSTALLATION.md     # Kurulum & Sorun Giderme
│   ├── FIND_INTEGRATION.md # Find.com.tr Çalışma Mantığı
│   └── API_REFERENCE.md    # REST API & WebSocket Referansı
└── frontend/               # React (TypeScript) + Vite Dashboard
    ├── src/
    │   ├── App.tsx         # Modern SaaS Dashboard & İnteraktif Tablo
    │   └── index.css       # Deep Carbon Glassmorphism Stilleri
    └── dist/               # Prodüksiyon Statik Varlıkları
```

---

## 📚 Detaylı Dokümantasyon

- [Sistem Mimarisi & Arama Algoritması](docs/ARCHITECTURE.md)
- [Kurulum & Hata Giderme Rehberi](docs/INSTALLATION.md)
- [Find.com.tr Entegrasyonu Nasıl Çalışır?](docs/FIND_INTEGRATION.md)
- [API & WebSocket Referansı](docs/API_REFERENCE.md)

---

## 📄 Lisans

Bu proje [MIT Lisansı](LICENSE) ile lisanslanmıştır. Veri gizliliği ve yerel kullanım için tasarlanmıştır.
