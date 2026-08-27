import re
from typing import Dict, Any, List, Optional
from urllib.parse import quote
from extractor import extract_phone_numbers
from name_cleaner import clean_company_variations

def lookup_company_on_find(company_name: str, location: Optional[str] = None) -> Dict[str, Any]:
    """
    Find.com.tr ve resmi veritabanı hızlı köprüsü.
    Anında yanıt üretir, doğrudan linkleri ve unvanı hazırlar.
    """
    variations = clean_company_variations(company_name)
    brand = variations[0] if variations else company_name
    clean_search = re.sub(r'\(.*?\)', '', str(brand)).strip()
    
    found_phones = []
    
    # Try fast snippet search if available
    try:
        from ddgs import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(f'site:find.com.tr "{clean_search}"', max_results=2, region="tr-tr"))
            for r in results:
                text = f"{r.get('title', '')} {r.get('body', '')}"
                phones = extract_phone_numbers(text)
                for p in phones:
                    if p not in found_phones:
                        found_phones.append(p)
    except Exception:
        pass

    direct_find_url = f"https://www.find.com.tr/Search?searchKey={quote(clean_search)}"
    direct_google_url = f"https://www.google.com/search?q={quote(clean_search + ' telefon iletişim')}"

    return {
        "company_name": company_name,
        "brand": clean_search,
        "candidate_phones": found_phones,
        "find_url": direct_find_url,
        "google_url": direct_google_url
    }
