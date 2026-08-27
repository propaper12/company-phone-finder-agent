import re
import html
from typing import List

# Temizlenecek resmi şirket unvan ekleri
COMPANY_SUFFIXES = [
    r'\banonim\s+şirketi\b', r'\banonim\s+şirket\b', r'\blimited\s+şirketi\b', r'\blimited\s+şirket\b',
    r'\ba\.?ş\.?\b', r'\bltd\.?\s*şti\.?\b', r'\bltd\.?\b', r'\bşti\.?\b',
    r'\bsanayi\s+ve\s+ticaret\b', r'\bsan\.\s*ve\s*tic\.\b', r'\bsan\.\s*tic\.\b', r'\bsanayi\s+ticaret\b',
    r'\bpazarlama\b', r'\bve\s+ticaret\b', r'\bticaret\b', r'\bsanayi\b',
    r'\bithalat\s+ihracat\b', r'\bith\.\s*ihr\.\b', r'\bve\s+hizmetleri\b', r'\bhizmetleri\b',
    r'\bholding\b', r'\bgroup\b', r'\bgrup\b', r'\byatırım\b', r'\btaşımacılık\b',
    r'\blojistik\b', r'\bdağıtım\b', r'\bve\s+danışmanlık\b', r'\bdanışmanlık\b'
]

def clean_company_variations(raw_name: str) -> List[str]:
    """
    Ham şirket adından en doğru marka adlarını ve sorgu varyasyonlarını üretir.
    Kısa kelimeleri (<=3 harf) tek başına bırakmaz, sektör kelimesiyle birleştirir.
    Örnek: 'ZEK BİLGİSAYAR SİSTEMLERİ...' -> ['Zek Bilgisayar', 'Zek Bilgisayar Sistemleri', ...]
    """
    if not raw_name:
        return []
        
    cleaned = str(raw_name).strip()
    cleaned = html.unescape(cleaned)
    cleaned = re.sub(r'[\r\n\t]+', ' ', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned)
    
    variations = []
    
    # 1. Parantez içindeki marka adını yakala: örn. (Hepsiburada), (Trendyol)
    paren_matches = re.findall(r'\(([^)]+)\)', cleaned)
    for p in paren_matches:
        p_clean = p.strip()
        if len(p_clean) >= 2 and not any(s in p_clean.lower() for s in ['a.ş', 'ltd', 'sanayi']):
            variations.append(p_clean)
            
    # Parantez dışındaki ana ismi al
    no_paren = re.sub(r'\([^)]*\)', '', cleaned).strip()
    
    # 2. Resmi ekleri temizle
    simplified = no_paren.lower()
    for suffix in COMPANY_SUFFIXES:
        simplified = re.sub(suffix, '', simplified, flags=re.IGNORECASE)
        
    simplified = re.sub(r'[.,\-_/\\()"\']', ' ', simplified)
    simplified = re.sub(r'\s+', ' ', simplified).strip()
    
    words = simplified.split()
    
    # Eğer ilk kelime 3 veya daha az harfse (örn: 'Zek', 'Öz', 'Ak'), tek başına bırakma!
    # En az ilk 2 kelimeyi al: 'Zek Bilgisayar'
    if len(words) >= 2:
        if len(words[0]) <= 3:
            brand = f"{words[0].upper()} {words[1].title()}"
        else:
            brand = " ".join(w.title() for w in words[:2])
        variations.append(brand)
    elif len(words) == 1:
        variations.append(words[0].title())
        
    if len(words) >= 3:
        three_words = " ".join(w.title() for w in words[:3])
        if three_words not in variations:
            variations.append(three_words)
            
    if simplified and len(simplified) >= 2:
        clean_title = simplified.title()
        if clean_title not in variations:
            variations.append(clean_title)
            
    # Orijinal tam unvanı da sona ekle
    variations.append(cleaned)
    
    return list(dict.fromkeys(variations))
