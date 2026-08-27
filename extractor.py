import re
import phonenumbers
from typing import List, Optional, Set

# Türkiye ve genel telefon numarası regex desenleri
PHONE_PATTERNS = [
    # 444'lü hatlar: 444 XX XX, 444 X XXX, 444XXXX
    re.compile(r'(?:\b|(?<=\s))(?:444\s*[\d\s]{4,6}\b)'),
    # 0850'li hatlar: 0850 XXX XX XX, +90 850 ...
    re.compile(r'(?:\+?90\s*[-.]?)?\(?0?850\)?\s*[\d\s.-]{7,12}\b'),
    # Türkiye alan kodları (0212, 0216, 0312, 0232 vb.): 0212 123 45 67, +90 212 123 4567
    re.compile(r'(?:\+?90\s*[-.]?)?\(?0?[2-4]\d{2}\)?\s*[\d\s.-]{7,12}\b'),
    # Cep telefonları (05xx): 0532 123 45 67, +90 532 123 4567
    re.compile(r'(?:\+?90\s*[-.]?)?\(?0?5\d{2}\)?\s*[\d\s.-]{7,12}\b'),
    # Genel uluslararası format (+90 ..., +1 ..., +44 ...)
    re.compile(r'\+\d{1,3}\s*(?:\(\d{1,4}\)|\d{1,4})[\s.-]*\d{2,4}[\s.-]*\d{2,4}(?:[\s.-]*\d{1,4})?'),
]

# Şirket olmayan ya da yanlış numara eşleşmelerini filtrelemek için kara liste
INVALID_STARTS = ('0000', '1234', '1111', '9999', '0101', '2020', '2021', '2022', '2023', '2024', '2025', '2026')

def clean_phone_number(num_str: str) -> str:
    """Numarayı temizler ve standartlaştırır."""
    if not num_str:
        return ""
    # tel: veya boşlukları temizle
    cleaned = re.sub(r'^[tT][eE][lL]:', '', num_str.strip())
    cleaned_digits = re.sub(r'[^\d+]', '', cleaned)
    
    # 444 ile başlıyorsa ve 7 haneliyse formatla: 444 XX XX
    if cleaned_digits.startswith('444') and len(cleaned_digits) == 7:
        return f"444 {cleaned_digits[3:5]} {cleaned_digits[5:]}"
    
    try:
        if cleaned_digits.startswith('+'):
            parsed = phonenumbers.parse(cleaned_digits, None)
        elif cleaned_digits.startswith('0'):
            parsed = phonenumbers.parse(cleaned_digits, "TR")
        elif len(cleaned_digits) == 10 and (cleaned_digits.startswith(('2', '3', '4', '5', '8'))):
            parsed = phonenumbers.parse('0' + cleaned_digits, "TR")
        elif len(cleaned_digits) == 11 and cleaned_digits.startswith('90'):
            parsed = phonenumbers.parse('+' + cleaned_digits, "TR")
        else:
            parsed = phonenumbers.parse(cleaned_digits, "TR")
            
        if phonenumbers.is_valid_number(parsed) or phonenumbers.is_possible_number(parsed):
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
    except Exception:
        pass
    
    return num_str.strip()

def is_valid_phone(num_str: str) -> bool:
    """Numaranın geçerli bir telefon olup olmadığını doğrular."""
    digits_only = re.sub(r'\D', '', num_str)
    
    # 444'lü hatlar 7 hanelidir
    if digits_only.startswith('444') and len(digits_only) == 7:
        return True
        
    # En az 10, en fazla 15 basamak olmalı
    if len(digits_only) < 10 or len(digits_only) > 15:
        return False
        
    for invalid in INVALID_STARTS:
        if digits_only.startswith(invalid):
            return False
            
    try:
        if num_str.startswith('+'):
            parsed = phonenumbers.parse(num_str, None)
        else:
            parsed = phonenumbers.parse(num_str, "TR")
        return phonenumbers.is_possible_number(parsed)
    except Exception:
        return 10 <= len(digits_only) <= 13

def extract_phone_numbers(text: str) -> List[str]:
    """
    Verilen metin / HTML içerisinden tüm telefon numaralarını ayıklar.
    """
    if not text:
        return []
        
    found_phones: Set[str] = set()
    
    # 1. Phonenumbers PhoneNumberMatcher ile bulma
    try:
        for match in phonenumbers.PhoneNumberMatcher(text, "TR"):
            num_formatted = phonenumbers.format_number(match.number, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
            if is_valid_phone(num_formatted):
                found_phones.add(num_formatted)
    except Exception:
        pass
        
    # 2. Özel Regex desenleri ile tarama
    for pattern in PHONE_PATTERNS:
        matches = pattern.findall(text)
        for match in matches:
            cleaned = clean_phone_number(match)
            if is_valid_phone(cleaned):
                found_phones.add(cleaned)
                
    # 3. Sıralama ve önceliklendirme (Kurumsal/sabit/0850/444 numaralarını öne al)
    result = list(found_phones)
    result.sort(key=lambda x: (
        0 if '444' in x or '850' in x else (
            1 if '+90 2' in x or '+90 3' in x or '+90 4' in x else 2
        )
    ))
    
    return result
