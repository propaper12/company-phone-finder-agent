import re
from typing import Dict, Any, Optional
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
from name_cleaner import clean_company_variations

try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS

from search_engine import fetch_page_content_fast, tr_lower, is_strictly_matched

def analyze_company_ai(company_name: str, location: Optional[str] = None, phone: Optional[str] = None, website: Optional[str] = None) -> Dict[str, Any]:
    """
    Şirket hakkında web üzerindeki kaynakları, kurumsal web sitesini ve ticaret verilerini
    analiz ederek yapılandırılmış yapay zeka istihbarat özeti üretir.
    Harici ücretli API anahtarı gerektirmez.
    """
    variations = clean_company_variations(company_name)
    brand = variations[0] if variations else company_name
    
    info = {
        "company_name": company_name,
        "brand": brand,
        "location": location or "Türkiye",
        "phone": phone or "Belirtilmemiş",
        "website": website or "—",
        "sector": "Genel Ticaret / Hizmet",
        "summary": "",
        "key_products": [],
        "source_snippets": []
    }
    
    # 1. Şirket hakkında web araması yap
    query = f'"{brand}" hakkında faaliyet alanı ürünler hizmetler'
    snippets = []
    
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=5, region="tr-tr", safesearch="off"))
            for r in results:
                title = r.get('title', '')
                body = r.get('body', '')
                url = r.get('href', '')
                if body:
                    snippets.append(f"{title}: {body}")
                    info["source_snippets"].append({"title": title, "snippet": body, "url": url})
                    if info["website"] == "—" and not any(d in url for d in ['find.com.tr', 'firmatlas.com', 'facebook', 'linkedin', 'instagram', 'sikayetvar']):
                        info["website"] = url
    except Exception:
        pass
        
    # 2. Eğer web sitesi varsa ana sayfa ve hakkımızda içeriğini oku
    site_text = ""
    if info["website"] != "—":
        site_text = fetch_page_content_fast(info["website"], timeout=4)
        if site_text:
            soup = BeautifulSoup(site_text, 'html.parser')
            for s in soup(['script', 'style', 'noscript', 'svg']):
                s.decompose()
            site_clean = soup.get_text(separator=' ', strip=True)
            if len(site_clean) > 100:
                site_text = site_clean[:2000]

    # 3. Sektör tespiti
    combined_corpus = (site_text + " " + " ".join(snippets)).lower()
    
    sector_rules = {
        "Yazılım, Bilişim & Finansal Teknoloji": ["yazılım", "bilişim", "fintek", "finansal teknoloji", "yapay zeka", "mobil uygulama", "saas", "teknoloji"],
        "Gıda, İçecek & Tarım": ["gıda", "tarım", "organik", "unlu mamul", "içecek", "et ürünleri", "süt", "market"],
        "İnşaat, Gayrimenkul & Yapı Malzemeleri": ["inşaat", "müteahhit", "yapı", "gayrimenkul", "konut", "mimarlık", "beton", "çimento"],
        "Tekstil, Konfeksiyon & Moda": ["tekstil", "giyim", "konfeksiyon", "kumaş", "iplik", "moda", "ayakkabı", "çanta"],
        "Lojistik, Taşımacılık & Kargo": ["kargo", "lojistik", "taşımacılık", "nakliyat", "depolama", "antrepo", "dağıtım"],
        "Sağlık, Medikal & İlaç": ["sağlık", "medikal", "ilaç", "hastane", "klinik", "tıbbi", "biyomedikal", "eczane"],
        "Otomotiv & Yan Sanayi": ["otomotiv", "araç", "yedek parça", "servis", "motorlu taşıtlar", "oto"],
        "Enerji, Elektrik & Çevre": ["enerji", "güneş enerjisi", "ges", "elektrik", "yenilenebilir", "rüzgar", "petrol"],
        "Mobilya, Dekorasyon & Ahşap": ["mobilya", "dekorasyon", "koltuk", "ahşap", "mutfak", "ofis mobilyası"],
        "Makine, Sanayi & İmalat": ["makine", "imalat", "sanayi", "üretim", "metal", "çelik", "döküm", "otomasyon"]
    }
    
    detected_sectors = []
    for sec_name, keywords in sector_rules.items():
        score = sum(1 for kw in keywords if kw in combined_corpus)
        if score > 0:
            detected_sectors.append((sec_name, score))
            
    if detected_sectors:
        detected_sectors.sort(key=lambda x: x[1], reverse=True)
        info["sector"] = detected_sectors[0][0]

    # 4. Yapay Zeka Özeti Oluştur
    if snippets or site_text:
        raw_desc = snippets[0] if snippets else site_text[:300]
        # Temizle
        raw_desc = re.sub(r'\s+', ' ', raw_desc).strip()
        info["summary"] = f"{brand}, {info['sector']} sektöründe faaliyet gösteren, {info['location']} merkezli bir kuruluştur. {raw_desc[:250]}..."
    else:
        info["summary"] = f"{brand}, Türkiye merkezli olarak {info['sector']} alanında faaliyet gösteren ticari bir kuruluştur."

    return info
