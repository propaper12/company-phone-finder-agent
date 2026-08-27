import asyncio
import aiohttp
import re
import time
from typing import Tuple, Optional, List
from bs4 import BeautifulSoup

from extractor import extract_phone_numbers, clean_phone_number, is_valid_phone
from name_cleaner import clean_company_variations

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
]

def extract_from_html_text(html_text: str) -> List[str]:
    if not html_text:
        return []
    soup = BeautifulSoup(html_text, 'html.parser')
    
    # 1. tel: linkleri
    for a in soup.find_all('a', href=True):
        href = a['href']
        if 'tel:' in href.lower():
            p = clean_phone_number(href)
            if is_valid_phone(p):
                return [p]
                
    # 2. Metin
    for s in soup(['script', 'style', 'noscript', 'svg']):
        s.decompose()
    text = soup.get_text(separator=' ', strip=True)
    return extract_phone_numbers(text)

async def async_search_single_company(
    session: aiohttp.ClientSession,
    company_name: str,
    deep_scan: bool = True
) -> Tuple[Optional[str], Optional[str]]:
    """
    Tek bir şirketi asenkron olarak milisaniyeler içinde arar.
    """
    variations = clean_company_variations(company_name)
    if not variations:
        return None, None
        
    primary_name = variations[0]
    
    # Öncelikli sorgu
    queries = [
        f'{primary_name} telefon OR iletişim OR 0850 OR 444 OR 0212 OR 0216',
        f'{primary_name} müşteri hizmetleri telefon',
    ]
    if len(variations) > 1:
        queries.append(f'"{variations[-1]}" telefon')

    candidate_urls = []

    for q in queries:
        try:
            # DuckDuckGo HTML / Lite hızlı endpoint
            url = "https://html.duckduckgo.com/html/"
            data = {'q': q}
            
            async with session.post(
                url,
                data=data,
                timeout=aiohttp.ClientTimeout(total=3.5),
                headers={'User-Agent': USER_AGENTS[hash(company_name) % len(USER_AGENTS)]}
            ) as resp:
                if resp.status == 200:
                    html_content = await resp.text()
                    soup = BeautifulSoup(html_content, 'html.parser')
                    
                    for r in soup.find_all('div', class_='result'):
                        snippet_elem = r.find('a', class_='result__snippet')
                        title_elem = r.find('a', class_='result__title')
                        url_elem = r.find('a', class_='result__url')
                        
                        snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
                        title = title_elem.get_text(strip=True) if title_elem else ""
                        href = url_elem.get('href', '') if url_elem else ""
                        
                        if href and href not in candidate_urls:
                            candidate_urls.append(href)
                            
                        phones = extract_phone_numbers(f"{title} {snippet}")
                        if phones:
                            return phones[0], href
        except Exception:
            pass

    # Derin tarama: İlk sitenin içeriğine asenkron olarak gir
    if deep_scan and candidate_urls:
        for site_url in candidate_urls[:2]:
            if any(skip in site_url for skip in ['facebook', 'instagram', 'linkedin', 'twitter', 'youtube', 'wikipedia']):
                continue
            try:
                async with session.get(
                    site_url,
                    timeout=aiohttp.ClientTimeout(total=3.0),
                    headers={'User-Agent': USER_AGENTS[0]},
                    ssl=False
                ) as page_resp:
                    if page_resp.status == 200:
                        page_html = await page_resp.text()
                        phones = extract_from_html_text(page_html)
                        if phones:
                            return phones[0], site_url
            except Exception:
                pass

    return None, None
