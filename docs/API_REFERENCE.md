# 🔌 API & WebSocket Referansı

FastAPI backend sunucusu tarafından sağlanan REST ve WebSocket uç noktaları aşağıda listelenmiştir.

---

## 1. REST Endpoints

### `GET /api/files`
Mevcut çalışma dizinindeki Excel ve CSV dosyalarını listeler.
- **Dönüş:** `{"files": ["5 - BİLGİ TEKNOLOJİLERİ - FAAL.xlsx", ...]}`

### `POST /api/upload`
Yeni bir Excel (`.xlsx`, `.xls`) veya CSV (`.csv`) dosyası yükler ve otomatik sütun analizi yapar.
- **Form Data:** `file: BinaryFile`
- **Dönüş:** Şirket sütunu, toplam satır, taranan satır sayısı vb. istatistikler.

### `POST /api/select_file?filename={filename}`
Belirtilen mevcut dosyayı seçer ve belleğe yükler.

### `GET /api/table`
İnteraktif tablo için sayfalanmış, filtrelenmiş ve sıralanmış veriyi döndürür.
- **Parametreler:**
  - `page` (int, varsayılan: 1)
  - `page_size` (int, varsayılan: 50)
  - `search` (string, arama sorgusu)
  - `filter_status` (`all` | `found` | `not_found` | `pending`)
  - `sort_by` (`found_first`)

### `POST /api/update_cell`
Tablodaki herhangi bir hücreyi günceller ve doğrudan Excel dosyasına yazar.
- **Body:**
  ```json
  {
    "row_index": 0,
    "column_name": "Bulunan_Telefon",
    "new_value": "+90 212 555 0101"
  }
  ```

### `POST /api/find_lookup`
Şirketi Find.com.tr ve rehberlerde sorgulayıp doğrudan linkleri ve aday numaraları getirir.
- **Body:**
  ```json
  {
    "company_name": "NOV FINANSAL TEKNOLOJI",
    "location": "Ataşehir / İstanbul"
  }
  ```

### `POST /api/ai_company_info`
Şirket hakkında faaliyet alanı, sektör ve yönetici özeti içeren yapay zeka istihbarat raporu üretir.

### `GET /api/download`
Sonuçların yer aldığı en güncel Excel dosyasını indirir.

---

## 2. WebSocket Protokolü

### `WS /ws/scan`

#### İstemciden Sunucuya Mesajlar:
```json
// Taramayı Başlatma
{
  "action": "start",
  "mode": "all" | "reset_all" | "unfound",
  "concurrency": 20,
  "deep_scan": false,
  "company_col": "Ünvan",
  "location_col": "Adres"
}

// Taramayı Durdurma
{
  "action": "stop"
}
```

#### Sunucudan İstemciye İlerleme Mesajları:
```json
{
  "type": "progress",
  "done_count": 150,
  "target_count": 5000,
  "total_rows": 15059,
  "completed_rows": 3200,
  "found_count": 2850,
  "not_found_count": 350,
  "success_rate": 89.1,
  "speed": 18.5,
  "latest_item": {
    "index": 149,
    "company": "Örnek Bilişim A.Ş.",
    "phone": "+90 216 444 0101",
    "url": "https://ornekbilisim.com/iletisim",
    "reason": "Resmi Web Sitesi Doğrulandı",
    "status": "Tamamlandı"
  }
}
```
