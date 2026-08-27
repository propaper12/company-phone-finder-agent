import re
import time
from typing import Optional, Tuple, List
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS

from extractor import extract_phone_numbers, clean_phone_number, is_valid_phone
from name_cleaner import clean_company_variations
from city_codes import get_city_code_from_location

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

JUNK_DOMAINS = [
    'hurdaci', 'sikayetvar', 'ciceksepeti', 'sahibinden', 'arabam', 'emlakjet',
    'hurriyetoto', 'n11', 'amazon', 'aliexpress', 'trendyol.com/butik',
    'hepsiburada.com/urun', 'eksisozluk', 'youtube', 'facebook', 'instagram',
    'tiktok', 'twitter', 'x.com', 'pinterest', 'kizlarsoruyor', 'memurlar.net',
    'donanimhaber', 'r10.net', 'wmaraci', 'technopat'
]

NON_OFFICIAL_DOMAINS = JUNK_DOMAINS + [
    'find.com.tr', 'firmatlas.com', 'bulurum.com', 'yellowpages.com.tr', 'b2bhint.com',
    'infobelpro.com', 'kompass.com', 'firmaturk.net', 'yenifirmalar.com', 'firmarehberim.com',
    'wikipedia.org'
]

http_session = requests.Session()
http_session.headers.update({'User-Agent': USER_AGENT})

def fetch_page_content_fast(url: str, timeout: int = 3) -> str:
    try:
        resp = http_session.get(url, timeout=timeout, verify=False)
        if resp.status_code == 200:
            return resp.text
    except Exception:
        pass
    return ""

def extract_from_html(html_content: str) -> List[str]:
    if not html_content:
        return []
    soup = BeautifulSoup(html_content, 'html.parser')
    
    tel_links = []
    for a in soup.find_all('a', href=True):
        href = a['href']
        if 'tel:' in href.lower():
            phone = clean_phone_number(href)
            if is_valid_phone(phone):
                tel_links.append(phone)
                
    if tel_links:
        return tel_links
        
    for s in soup(['script', 'style', 'noscript', 'svg']):
        s.decompose()
    page_text = soup.get_text(separator=' ', strip=True)
    return extract_phone_numbers(page_text)

def tr_lower(text: str) -> str:
    if not text:
        return ""
    return str(text).replace('İ', 'i').replace('I', 'ı').lower()

def is_strictly_matched(company_name: str, title: str, snippet: str, url: str) -> bool:
    url_lower = str(url).lower()
    comp_clean = tr_lower(company_name)
    
    for junk in JUNK_DOMAINS:
        if junk in url_lower and junk not in comp_clean:
            return False
            
    combined = tr_lower(f"{title} {snippet} {url}")
    result_tokens = set(re.findall(r'\b[a-z0-9ğüşıöç]{2,}\b', combined))
    
    ignored = {
        've', 'ile', 'sanayi', 'ticaret', 'anonim', 'limited', 'şirketi', 'sirketi', 
        'şti', 'sti', 'a.ş', 'ltd', 'san', 'tic', 'pazarlama', 'ithalat', 'ihracat'
    }
    
    comp_words = [w for w in re.findall(r'\b[a-z0-9ğüşıöç]{2,}\b', comp_clean) if w not in ignored]
    
    if not comp_words:
        return True
        
    first_brand_word = comp_words[0]
    
    if first_brand_word not in result_tokens:
        return False
        
    if len(comp_words) >= 2:
        other_words = set(comp_words[1:])
        if not other_words.intersection(result_tokens):
            return False
            
    return True

def filter_and_prioritize_by_location(phones: List[str], location_str: Optional[str]) -> List[str]:
    if not phones or not location_str:
        return phones
        
    city_codes = get_city_code_from_location(location_str)
    if not city_codes:
        return phones
        
    def score_phone(num: str) -> int:
        digits = re.sub(r'\D', '', num)
        for code in city_codes:
            if digits.startswith(('90' + code, '0' + code, code)):
                return 0
        if '850' in num or '444' in num:
            return 1
        return 2

    return sorted(phones, key=score_phone)

def find_official_website_and_extract_phone(company_name: str, location: Optional[str] = None) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    variations = clean_company_variations(company_name)
    if not variations:
        return None, None, None
        
    brand = variations[0]
    queries = [
        f'"{brand}" resmi web sitesi',
        f'"{brand}" iletişim',
        f'"{brand}"'
    ]
    
    candidate_domains = []
    
    try:
        with DDGS(timeout=4) as ddgs:
            for q in queries:
                results = list(ddgs.text(q, max_results=4, region="tr-tr", safesearch="off"))
                for r in results:
                    url = r.get('href', '')
                    title = r.get('title', '')
                    snippet = r.get('body', '')
                    
                    if not is_strictly_matched(company_name, title, snippet, url):
                        continue
                        
                    domain = urlparse(url).netloc.lower()
                    if any(non in domain for non in NON_OFFICIAL_DOMAINS):
                        continue
                        
                    if url and url not in candidate_domains:
                        candidate_domains.append(url)
                if candidate_domains:
                    break
    except Exception:
        pass

    had_website = False
    for site_url in candidate_domains[:2]:
        had_website = True
        try:
            resp = http_session.get(site_url, timeout=4, verify=False)
            if resp.status_code != 200:
                continue
                
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            phones = extract_from_html(resp.text)
            if phones:
                sorted_phones = filter_and_prioritize_by_location(phones, location)
                return sorted_phones[0], site_url, None
                
            contact_links = []
            for a in soup.find_all('a', href=True):
                href = a['href']
                text = a.get_text().lower()
                if any(kw in href.lower() or kw in text for kw in ['iletisim', 'contact', 'bize-ulasin', 'bize_ulasin', 'hakkimizda', 'subeler']):
                    full_url = urljoin(site_url, href)
                    if urlparse(full_url).netloc == urlparse(site_url).netloc:
                        contact_links.append(full_url)
                        
            for c_url in list(dict.fromkeys(contact_links))[:2]:
                c_resp = http_session.get(c_url, timeout=3, verify=False)
                if c_resp.status_code == 200:
                    c_phones = extract_from_html(c_resp.text)
                    if c_phones:
                        sorted_phones = filter_and_prioritize_by_location(c_phones, location)
                        return sorted_phones[0], c_url, None
        except Exception:
            pass

    return None, None, "Web sitesi bulundu ancak açık telefon numarası (sadece form/e-posta) yer almıyor" if had_website else None

def search_company_phone_deep(
    company_name: str, 
    location: Optional[str] = None, 
    officer: Optional[str] = None,
    deep_scan_sites: bool = True
) -> Tuple[Optional[str], Optional[str], str]:
    """
    4 KADEMELİ ULTRA HASSAS TÜRKİYE ŞİRKET TELEFON BULUCU & TEŞHİS MOTORU
    Dönüş: (phone, url, reason)
    """
    variations = clean_company_variations(company_name)
    if not variations:
        return None, None, "Geçersiz şirket unvanı"
        
    primary_name = variations[0]
    
    loc_clean = ""
    if location and str(location).strip() and str(location).strip().lower() not in ['nan', 'none', '—']:
        loc_clean = " ".join(str(location).strip().split()[:2])

    officer_clean = ""
    if officer and str(officer).strip() and str(officer).strip().lower() not in ['nan', 'none', '—']:
        officer_clean = str(officer).strip()

    candidate_urls = []
    matched_homonyms = False

    # 1. AŞAMA: FİRMA REHBERLERİ (Find.com.tr, Firmatlas, Bulurum)
    directory_queries = [
        f'site:find.com.tr "{primary_name}"',
        f'site:firmatlas.com "{primary_name}"',
        f'site:bulurum.com "{primary_name}"'
    ]
    
    try:
        with DDGS(timeout=4) as ddgs:
            for q in directory_queries:
                results = list(ddgs.text(q, max_results=2, region="tr-tr", safesearch="off"))
                for item in results:
                    title = item.get('title', '')
                    snippet = item.get('body', '')
                    url = item.get('href', '')
                    
                    if not is_strictly_matched(company_name, title, snippet, url):
                        matched_homonyms = True
                        continue
                        
                    phones = extract_phone_numbers(f"{title} {snippet}")
                    if phones:
                        sorted_phones = filter_and_prioritize_by_location(phones, location)
                        return sorted_phones[0], url, "Find.com.tr / Rehber Önbelleği Doğrulandı"
                        
                    html = fetch_page_content_fast(url)
                    if html:
                        page_phones = extract_from_html(html)
                        if page_phones:
                            sorted_phones = filter_and_prioritize_by_location(page_phones, location)
                            return sorted_phones[0], url, "Find.com.tr / Rehber Kaydı Doğrulandı"
    except Exception:
        pass

    # 2. AŞAMA: LOKASYON & YETKİLİ ODAKLI ARAMA
    general_queries = []
    if loc_clean:
        general_queries.append(f'"{primary_name}" {loc_clean} telefon')
        general_queries.append(f'"{primary_name}" {loc_clean} iletişim')
    else:
        general_queries.append(f'"{primary_name}" telefon')
        general_queries.append(f'"{primary_name}" iletişim')
        
    if len(variations) > 1:
        general_queries.append(f'"{variations[1]}" telefon')

    if officer_clean:
        general_queries.append(f'"{primary_name}" "{officer_clean}"')

    try:
        with DDGS(timeout=4) as ddgs:
            for q in general_queries:
                results = list(ddgs.text(q, max_results=3, region="tr-tr", safesearch="off"))
                if not results:
                    continue
                    
                for item in results:
                    title = item.get('title', '')
                    snippet = item.get('body', '')
                    url = item.get('href', '')
                    
                    if not is_strictly_matched(company_name, title, snippet, url):
                        matched_homonyms = True
                        continue
                        
                    if url and url not in candidate_urls:
                        candidate_urls.append(url)
                        
                    combined_text = f"{title} {snippet}"
                    phones = extract_phone_numbers(combined_text)
                    if phones:
                        sorted_phones = filter_and_prioritize_by_location(phones, location)
                        return sorted_phones[0], url, "Arama Dizini Doğrulandı"

    except Exception:
        pass

    # 3. AŞAMA: RESMİ WEB SİTESİ VE İLETİŞİM SAYFASI
    phone, site_url, site_reason = find_official_website_and_extract_phone(company_name, location)
    if phone:
        return phone, site_url, "Resmi Web Sitesi / İletişim Sayfası Doğrulandı"

    if deep_scan_sites and candidate_urls:
        for url in candidate_urls[:2]:
            html = fetch_page_content_fast(url)
            if html:
                phones = extract_from_html(html)
                if phones:
                    sorted_phones = filter_and_prioritize_by_location(phones, location)
                    return sorted_phones[0], url, "Web Sayfası Doğrulandı"

    # TEŞHİS / BULUNAMAMA NEDENİ BELİRLEME
    if site_reason:
        return None, None, site_reason
    if matched_homonyms:
        return None, None, "Adaş şirketler tespit edildi ancak ilçe/bölge kodu uyuşmadığı için güvenlik gereği elendi"
    if officer_clean:
        return None, None, "Şahıs/Küçük işletme - Halka açık resmi kayıtlarda telefon yayınlanmamış"
    return None, None, "Açık web sitesi veya doğrulanmış rehber kaydı bulunamadı (Askıda/Tasfiyede olabilir)"
