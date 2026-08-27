# 🔍 Find.com.tr Entegrasyonu & Paywall Aşma Mekanizması

Bu dokümanda **Find.com.tr** ve benzeri Türkiye firma rehberlerinin nasıl tarandığı ve arayüzdeki doğrudan arama entegrasyonu açıklanmıştır.

---

## 💰 Ücret Duvarı (Paywall) Nasıl Aşılır?

`find.com.tr`, `firmatlas.com` ve `yellowpages.com.tr` gibi rehber siteleri normal bir kullanıcı tarayıcıdan girdiğinde telefon numarasının üzerini kapatıp *"Numarayı görmek için abone olun / Kredi satın alın"* der.

### Agentımızın Çalışma Prensibi:
1. **Açık Arama Motoru İndeksleri:** Bu platformlar Google ve arama motorlarında üst sıralara çıkabilmek için şirket telefonlarını, adreslerini ve sicil bilgilerini arka planda `Schema.org / JSON-LD`, `meta tags` ve arama botlarına açık **HTML kaynak kodunda yayınlamak zorundadır**.
2. **Doğrulanmış Snippet Taraması:** Agent doğrudan o sitenin "numarayı göster" butonuna tıklamak yerine, arama motorlarının dizine eklediği **resmi ve doğrulanmış önbellek metinlerini** tarar.
3. **Çapraz Doğrulama:** Numara sadece Find'dan değil; `Firmatlas`, `Bulurum`, `B2BHint`, `Ticaret Sicil özetleri` ve şirketin kendi **resmi web sitesi footer'ı** ile çapraz eşleştirilir.

---

## 🎯 Arayüzdeki 1-Tıkla Find.com.tr Modalı

Kullanıcı arayüzde herhangi bir satırın yanındaki **`🔍 Find'da Ara`** butonuna bastığında:

1. **Unvan Temizleme:** Şirket adındaki `A.Ş.`, `Ltd. Şti.`, `San. ve Tic.` gibi ekler temizlenerek ana marka adı izole edilir.
2. **Find.com.tr Hızlı Penceresi:**
   - Şirketin doğrudan Find.com.tr arama sayfası açılır (`https://www.find.com.tr/Search?searchKey=...`).
   - Sistem önbellekten yakaladığı numaraları yeşil butonla **`✓ [Numara] ➔ Satıra Yaz`** şeklinde önerir.
3. **Anında Excel'e Kayıt:**
   - Kullanıcı numarayı onayladığı veya kutucuğa yazıp **`💾 Bu Numarayı Kaydet`** dediği anda:
     - Değer anında **Excel dosyasındaki o satıra yazılır**.
     - Durumu **`Tamamlandı`** olarak güncellenir.
