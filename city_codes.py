from typing import Optional, List

# Türkiye İl Telefon Alan Kodları Haritası
CITY_AREA_CODES = {
    'adana': ['322'], 'adıyaman': ['416'], 'afyon': ['272'], 'afyonkarahisar': ['272'],
    'ağrı': ['472'], 'amasya': ['358'], 'ankara': ['312'], 'antalya': ['242'],
    'artvin': ['466'], 'aydın': ['256'], 'balıkesir': ['266'], 'bilecik': ['228'],
    'bingöl': ['426'], 'bitlis': ['434'], 'bolu': ['374'], 'burdur': ['248'],
    'bursa': ['224'], 'çanakkale': ['286'], 'çankırı': ['376'], 'çorum': ['364'],
    'denizli': ['258'], 'diyarbakır': ['412'], 'edirne': ['284'], 'elazığ': ['424'],
    'erzincan': ['446'], 'erzurum': ['442'], 'eskişehir': ['222'], 'gaziantep': ['342'],
    'giresun': ['454'], 'gümüşhane': ['456'], 'hakkari': ['438'], 'hatay': ['326'],
    'ısparta': ['246'], 'mersin': ['324'], 'içel': ['324'], 'istanbul': ['212', '216'],
    'izmir': ['232'], 'kars': ['474'], 'kastamonu': ['366'], 'kayseri': ['352'],
    'kırklareli': ['288'], 'kırşehir': ['386'], 'kocaeli': ['262'], 'izmit': ['262'],
    'konya': ['332'], 'kütahya': ['274'], 'malatya': ['422'], 'manisa': ['236'],
    'kahramanmaraş': ['344'], 'maraş': ['344'], 'mardin': ['482'], 'muğla': ['252'],
    'muş': ['436'], 'nevşehir': ['384'], 'niğde': ['388'], 'ordu': ['452'],
    'rize': ['464'], 'sakarya': ['264'], 'adapazarı': ['264'], 'samsun': ['362'],
    'siirt': ['484'], 'sinop': ['368'], 'sivas': ['346'], 'tekirdağ': ['282'],
    'tokat': ['356'], 'trabzon': ['462'], 'tunceli': ['428'], 'şanlıurfa': ['414'],
    'urfa': ['414'], 'uşak': ['276'], 'van': ['432'], 'yozgat': ['354'],
    'zonguldak': ['372'], 'aksaray': ['382'], 'bayburt': ['458'], 'karaman': ['338'],
    'kırıkkale': ['318'], 'batman': ['488'], 'şırnak': ['486'], 'bartın': ['378'],
    'ardahan': ['478'], 'ığdır': ['476'], 'yalova': ['226'], 'karabük': ['370'],
    'kilis': ['348'], 'osmaniye': ['328'], 'düzce': ['380']
}

def get_city_code_from_location(location_str: str) -> List[str]:
    """Adres veya şehir metninden il alan kodlarını çıkarır."""
    if not location_str:
        return []
    loc_clean = str(location_str).lower()
    codes = []
    for city, code_list in CITY_AREA_CODES.items():
        if city in loc_clean:
            codes.extend(code_list)
    return list(dict.fromkeys(codes))
