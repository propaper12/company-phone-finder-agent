import os
import re
import pandas as pd
from typing import Optional, Tuple, List

POSSIBLE_COMPANY_COLUMNS = [
    'ünvan', 'unvan', 'unvanı', 'ünvanı', 'ticari unvan', 'ticari ünvan',
    'şirket', 'sirket', 'şirket adı', 'sirket adi', 'şirket_adı', 'sirket_adi',
    'firma', 'firma adı', 'firma adi', 'firma_adı', 'firma_adi',
    'company', 'company name', 'company_name', 'name', 'title'
]

EXCLUDED_COLUMN_KEYWORDS = [
    'sicil', 'no', 'kod', 'nace', 'tarih', 'faks', 'vergi', 'tc', 'id'
]

POSSIBLE_LOCATION_COLUMNS = [
    'ilçe', 'ilce', 'şehir', 'sehir', 'il', 'il/ilçe', 'il_ilce',
    'adres', 'address', 'açık adres', 'acik adres', 'konum', 'location',
    'bölge', 'bolge', 'city', 'province', 'state'
]

POSSIBLE_OFFICER_COLUMNS = [
    'yetkili 1', 'yetkili', 'yetkili adi', 'yetkili_adi', 'yetkili kişi',
    'ortak', 'yonetici', 'yönetici', 'sahip', 'officer', 'manager'
]

def normalize_col(text: str) -> str:
    if not text:
        return ""
    t = str(text).strip().lower()
    t = t.replace('ı', 'i').replace('İ', 'i').replace('ü', 'u').replace('ö', 'o').replace('ş', 's').replace('ç', 'c').replace('ğ', 'g')
    return t

class ExcelManager:
    def __init__(self, input_file: str, output_file: Optional[str] = None):
        self.input_file = input_file
        if output_file:
            self.output_file = output_file
        else:
            base, ext = os.path.splitext(input_file)
            self.output_file = f"{base}_telefon_sonuclari{ext if ext in ['.xlsx', '.xls', '.csv'] else '.xlsx'}"
            
        self.df = None
        self.company_col = None
        self.location_col = None
        self.officer_col = None
        self.load_data()

    def load_data(self):
        target_path = self.output_file if os.path.exists(self.output_file) else self.input_file
        
        if target_path.endswith('.csv'):
            self.df = pd.read_csv(target_path, dtype=str)
        else:
            self.df = pd.read_excel(target_path, dtype=str)
            
        if 'Bulunan_Telefon' not in self.df.columns:
            self.df['Bulunan_Telefon'] = ""
        if 'Telefon_Kaynak_URL' not in self.df.columns:
            self.df['Telefon_Kaynak_URL'] = ""
        if 'Neden_Bulunamadi' not in self.df.columns:
            self.df['Neden_Bulunamadi'] = ""
        if 'Durum' not in self.df.columns:
            self.df['Durum'] = "Bekliyor"
            
        self.df = self.df.fillna("")

    def reset_all_rows(self):
        self.df['Bulunan_Telefon'] = ""
        self.df['Telefon_Kaynak_URL'] = ""
        self.df['Neden_Bulunamadi'] = ""
        self.df['Durum'] = "Bekliyor"
        self.save()

    def detect_company_column(self, specified_col: Optional[str] = None) -> str:
        if specified_col and specified_col in self.df.columns:
            self.company_col = specified_col
            return specified_col
            
        for col in self.df.columns:
            norm = normalize_col(col)
            if any(exc in norm for exc in EXCLUDED_COLUMN_KEYWORDS):
                continue
            if norm in ['unvan', 'unvani', 'firma', 'firma adi', 'sirket', 'sirket adi', 'company', 'company name']:
                self.company_col = col
                return col
                
        for col in self.df.columns:
            norm = normalize_col(col)
            if any(exc in norm for exc in EXCLUDED_COLUMN_KEYWORDS):
                continue
            if any(key in norm for key in ['unvan', 'sirket', 'firma', 'company']):
                self.company_col = col
                return col
                
        for col in self.df.columns:
            norm = normalize_col(col)
            if any(exc in norm for exc in EXCLUDED_COLUMN_KEYWORDS):
                continue
            self.company_col = col
            return col
                
        self.company_col = self.df.columns[0]
        return self.company_col

    def detect_location_column(self, specified_col: Optional[str] = None) -> Optional[str]:
        if specified_col and specified_col in self.df.columns:
            self.location_col = specified_col
            return specified_col
            
        for col in self.df.columns:
            norm = normalize_col(col)
            if norm in ['ilce', 'sehir', 'il', 'il/ilce']:
                self.location_col = col
                return col
                
        for col in self.df.columns:
            norm = normalize_col(col)
            if 'adres' in norm and norm != normalize_col(self.company_col):
                self.location_col = col
                return col
                
        return None

    def detect_officer_column(self, specified_col: Optional[str] = None) -> Optional[str]:
        if specified_col and specified_col in self.df.columns:
            self.officer_col = specified_col
            return specified_col
            
        for col in self.df.columns:
            norm = normalize_col(col)
            if any(key in norm for key in POSSIBLE_OFFICER_COLUMNS):
                self.officer_col = col
                return col
        return None

    def get_pending_indices(self) -> List[int]:
        pending = []
        for idx, row in self.df.iterrows():
            durum = str(row.get('Durum', '')).strip()
            tel = str(row.get('Bulunan_Telefon', '')).strip()
            if durum == "Bekliyor" or (durum != "Tamamlandı" and durum != "Bulunamadı" and not tel):
                pending.append(idx)
        return pending

    def get_unfound_indices(self) -> List[int]:
        unfound = []
        for idx, row in self.df.iterrows():
            durum = str(row.get('Durum', '')).strip()
            tel = str(row.get('Bulunan_Telefon', '')).strip()
            if durum == "Bulunamadı" and not tel:
                unfound.append(idx)
        return unfound

    def update_row(self, index: int, phone: Optional[str], url: Optional[str], reason: str = ""):
        if phone:
            self.df.at[index, 'Bulunan_Telefon'] = phone
            self.df.at[index, 'Telefon_Kaynak_URL'] = url or ""
            self.df.at[index, 'Neden_Bulunamadi'] = "Doğrulandı (Başarılı)"
            self.df.at[index, 'Durum'] = "Tamamlandı"
        else:
            self.df.at[index, 'Neden_Bulunamadi'] = reason or "Açık dijital kayıt bulunamadı"
            self.df.at[index, 'Durum'] = "Bulunamadı"

    def save(self):
        temp_file = f"{self.output_file}.tmp"
        try:
            if self.output_file.endswith('.csv'):
                self.df.to_csv(temp_file, index=False, encoding='utf-8-sig')
            else:
                self.df.to_excel(temp_file, index=False, engine='openpyxl')
                
            if os.path.exists(self.output_file):
                os.remove(self.output_file)
            os.rename(temp_file, self.output_file)
        except Exception:
            if self.output_file.endswith('.csv'):
                self.df.to_csv(self.output_file, index=False, encoding='utf-8-sig')
            else:
                self.df.to_excel(self.output_file, index=False, engine='openpyxl')
