import os
import sys
import time
import signal
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from tqdm import tqdm

# Windows terminal UTF-8 desteği
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

from excel_manager import ExcelManager
from search_engine import search_company_phone_fast

class PhoneFinderAgent:
    def __init__(self, input_file: str, output_file: str = None, company_column: str = None, location_column: str = None, max_workers: int = 15, save_batch: int = 20):
        self.manager = ExcelManager(input_file, output_file)
        self.company_col = self.manager.detect_company_column(company_column)
        self.location_col = self.manager.detect_location_column(location_column)
        self.max_workers = max_workers
        self.save_batch = save_batch
        self.lock = Lock()
        self.is_running = True
        self.found_count = 0
        self.not_found_count = 0
        self.counter = 0

        # Ctrl+C sinyali yakalama
        signal.signal(signal.SIGINT, self._handle_interrupt)

    def _handle_interrupt(self, sig, frame):
        print("\n\n[!] Durdurma isteği alındı. Mevcut ilerleme kaydediliyor...")
        self.is_running = False
        with self.lock:
            self.manager.save()
        print(f"[✓] İlerleme başarıyla kaydedildi: {self.manager.output_file}")
        print("[✓] Programı tekrar başlattığınızda kaldığı yerden devam edecektir.")
        sys.exit(0)

    def _process_single_company(self, idx: int, company_name: str, location_val: str = None):
        if not self.is_running:
            return idx, None, None
        phone, url = search_company_phone_deep(company_name, location=location_val, deep_scan_sites=False)
        return idx, phone, url

    def run(self):
        print("=" * 60)
        print("⚡ 10K ŞİRKET TELEFON BULUCU AGENT (TURBO HIZ)")
        print("=" * 60)
        print(f"📁 Giriş Dosyası      : {self.manager.input_file}")
        print(f"💾 Çıktı Dosyası     : {self.manager.output_file}")
        print(f"🔍 Şirket Sütunu     : {self.company_col}")
        print(f"⚡ Eşzamanlı Worker  : {self.max_workers}")
        print("=" * 60)

        pending_indices = self.manager.get_pending_indices()
        total_rows = len(self.manager.df)
        already_done = total_rows - len(pending_indices)

        if not pending_indices:
            print("[✓] Tüm satırlar zaten işlenmiş! Yapılacak işlem yok.")
            return

        print(f"📊 Toplam: {total_rows:,} | Zaten İşlenmiş: {already_done:,} | Kalan: {len(pending_indices):,}\n")

        pbar = tqdm(total=len(pending_indices), desc="⚡ Turbo Arama", unit="şirket")

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_idx = {
                executor.submit(
                    self._process_single_company,
                    idx,
                    str(self.manager.df.at[idx, self.company_col])
                ): idx for idx in pending_indices
            }

            for future in as_completed(future_to_idx):
                if not self.is_running:
                    break

                try:
                    idx, phone, url = future.result()
                    with self.lock:
                        self.manager.update_row(idx, phone, url)
                        self.counter += 1
                        
                        if phone:
                            self.found_count += 1
                        else:
                            self.not_found_count += 1

                        if self.counter % self.save_batch == 0:
                            self.manager.save()

                    # İlerleme çubuğunu güncelle
                    total_done = self.found_count + self.not_found_count
                    pbar.set_postfix({
                        "Bulunan": self.found_count,
                        "Bulunamayan": self.not_found_count,
                        "Başarı %": f"{(self.found_count / total_done * 100):.1f}%" if total_done > 0 else "0%"
                    })
                    pbar.update(1)

                except Exception:
                    pbar.update(1)

        pbar.close()

        # Son durumu kaydet
        with self.lock:
            self.manager.save()

        print("\n" + "=" * 60)
        print("🎉 İŞLEM TAMAMLANDI!")
        print(f"✅ Toplam Bulunan Telefon   : {self.found_count:,}")
        print(f"❌ Bulunamayan              : {self.not_found_count:,}")
        print(f"📂 Sonuç Dosyası             : {self.manager.output_file}")
        print("=" * 60)

def main():
    parser = argparse.ArgumentParser(description="10K Şirket Telefon Numarası Bulma Agent'ı (Turbo)")
    parser.add_argument("--file", "-f", help="İşlenecek Excel veya CSV dosyasının yolu")
    parser.add_argument("--column", "-c", help="Şirket adlarının bulunduğu sütun adı")
    parser.add_argument("--workers", "-w", type=int, default=15, help="Eşzamanlı iş parçacığı sayısı (Varsayılan: 15)")
    parser.add_argument("--output", "-o", help="Çıktı dosyasının yolu")
    
    args = parser.parse_args()

    file_path = args.file
    if not file_path:
        files = [f for f in os.listdir('.') if f.endswith(('.xlsx', '.xls', '.csv')) and not f.endswith(('_telefon_sonuclari.xlsx', '_telefon_sonuclari.csv'))]
        if files:
            file_path = files[0]
            print(f"[i] Otomatik dosya bulundu: {file_path}")
        else:
            print("[!] Lütfen işlenecek Excel/CSV dosyasını belirtin:")
            print("    Kullanım: python agent.py --file sirketler.xlsx")
            return

    agent = PhoneFinderAgent(
        input_file=file_path,
        output_file=args.output,
        company_column=args.column,
        max_workers=args.workers
    )
    agent.run()

if __name__ == "__main__":
    main()
