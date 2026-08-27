# ⚡ 10K Şirket Telefon & AI İstihbarat Agent - Kurulum ve Kullanım Kılavuzu

Bu yazılım, elinizdeki binlerce şirketin yer aldığı Excel listelerini (unvan ve adresleri) tarayarak **Find.com.tr, Firmatlas, Bulurum, Google ve Şirketlerin Resmi Web Siteleri** üzerinden gerçek telefon numaralarını en yüksek doğrulukla bulan **otonom bir yapay zeka ve arama motorudur**.

---

## 🚀 TEK TIKLA KURULUM VE ÇALIŞTIRMA (1 Dakika)

1. Klasördeki **`KURULUM_VE_BASLAT.bat`** (veya `baslat.bat`) dosyasına **çift tıklayın**.
2. Sistem tüm Python kütüphanelerini otomatik olarak kontrol eder, eksikleri yükler.
3. Sunucu açılır ve varsayılan internet tarayıcınızda otomatik olarak **http://127.0.0.1:8000** sayfası açılır!

*(Eğer bilgisayarınızda Python yüklü değilse [Python.org](https://www.python.org/downloads/) adresinden indirip kurarken **"Add Python to PATH"** kutucuğunu işaretlemeyi unutmayın).*

---

## 📖 ADIM ADIM KULLANIM REHBERİ

### 1. Dosya Yükleme veya Seçme
* Sayfa açıldığında sol paneldeki açılır listeden mevcut dosyalardan birini seçin (Örn: `5 - BİLGİ TEKNOLOJİLERİ - FAAL.xlsx`) veya kendi Excel/CSV dosyanızı kutucuğa sürükleyin.
* **Şirket Sütunu:** Otomatik olarak `Ünvan` seçilecektir.
* **Şehir / Adres:** `Adres` veya `İlçe` seçildiğinden emin olun.

### 2. Hız (Worker) Ayarı
* Orta paneldeki **Eşzamanlı Worker** kaydırıcısını **20 veya 25 Worker** seviyesine getirin (Maksimum hızda paralel tarama yapar).

### 3. Taramayı Başlatma
* **`🚀 Kalanları Tara`**: Daha önce taranmamış veya bekleyen şirketleri kaldığı yerden tarar.
* **`🔁 Tümünü Sıfırdan Baştan Tara`**: Tüm listeyi temizler ve en baştan itibaren taramaya başlar.
* **`🔄 Sadece Bulunamayanları Tara`**: Daha önce taranıp numarası bulunamamış olanları derin taramaya alır.

### 4. Canlı İzleme & Hata Teşhisi
* **`⚡ Canlı Radar`** sekmesinden anlık tarama hızını, başarı oranını ve her şirket için neden bulunamadığına dair **teşhis açıklamasını** (Adaş şirket eleme, açık numara yok, sadece e-posta var vb.) izleyebilirsiniz.

### 5. Find.com.tr Doğrudan Arama & 1-Tıkla Numara Girişi
* **`📊 İnteraktif Excel Tablosu`** sekmesine geçin.
* Numarası olmayan veya kontrol etmek istediğiniz şirketin yanındaki **`🔍 Find'da Ara`** butonuna basın.
* Açılan modalda Find.com.tr sayfasını doğrudan açabilir, gördüğünüz numarayı yazıp **`💾 Bu Numarayı Kaydet`** butonuna basarak anında Excel tablosuna işleyebilirsiniz.

### 6. Excel Sonuçlarını İndirme
* Tarama bittiğinde (veya tarama sürerken istediğiniz anda) sağ üstteki yeşil **`📥 Güncel Excel İndir`** butonuna basarak numaraları doldurulmuş ve teşhis raporu eklenmiş güncel Excel dosyanızı indirebilirsiniz.

---

## 🛡️ GÜVENLİK VE GÜVENCELER

* **Otomatik Kayıt (Checkpoint):** Elektrik, bilgisayar veya internet kesilse bile sistem her 15 satırda bir Excel'e otomatik kaydeder. Asla veri kaybı yaşanmaz.
* **%100 Yerel ve Gizli:** Excel dosyanızdaki veriler asla dış sunuculara gönderilmez, tamamen kendi bilgisayarınızda yerel çalışır.
