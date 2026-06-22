import os
import re
import ipaddress
import requests
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs
from concurrent.futures import ThreadPoolExecutor, as_completed

# ===================== ИСТОЧНИКИ =====================
SOURCES = [
    "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/WHITE-CIDR-RU-checked.txt",
    "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/Vless-Reality-White-Lists-Rus-Mobile.txt",
    "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/Vless-Reality-White-Lists-Rus-Mobile-2.txt",
    "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/WHITE-SNI-RU-all.txt",
    "https://raw.githubusercontent.com/whoahaow/rjsxrd/refs/heads/main/githubmirror/bypass/bypass-all.txt",
    "https://raw.githubusercontent.com/ShatakVPN/ConfigForge-V2Ray/main/configs/all.txt",
    "https://raw.githubusercontent.com/ShatakVPN/ConfigForge-V2Ray/main/configs/light.txt",
    "https://raw.githubusercontent.com/ShatakVPN/ConfigForge-V2Ray/main/configs/vless.txt",
    "https://raw.githubusercontent.com/MahanKenway/Freedom-V2Ray/main/configs/mix.txt",
    "https://raw.githubusercontent.com/MahanKenway/Freedom-V2Ray/main/configs/vless.txt",
    "https://raw.githubusercontent.com/kort0881/vpn-checker-backend/main/checked/RU_Best/ru_white.txt",
    "https://raw.githubusercontent.com/zieng2/wl/refs/heads/main/vless_lite.txt",
]
for i in range(1, 21):
    SOURCES.append(
        f"https://raw.githubusercontent.com/AvenCores/goida-vpn-configs/refs/heads/main/githubmirror/{i}.txt"
    )

# ===================== НАСТРОЙКИ =====================
ALLOWED_CIDRS = []
WHITELISTED_SNI = []
IS_PUBLIC = True
LIMIT = 3000  # Жесткий лимит конфигов прямо в коде

CONFIG_FILE = "YaltaVPN - Subscription"  
LOG_FILE = "log.csv"
BASE_DIR = os.path.abspath(os.getcwd())

# ===================== СТРАНЫ =====================
FLAG_TO_CODE = {
    "🇦🇫": "AF", "🇦🇱": "AL", "🇩🇿": "DZ", "🇦🇩": "AD", "🇦🇴": "AO",
    "🇦🇷": "AR", "🇦🇲": "AM", "🇦🇺": "AU", "🇦🇹": "AT", "🇦🇿": "AZ",
    "🇧🇩": "BD", "🇧🇾": "BY", "🇧🇪": "BE", "🇧🇷": "BR", "🇧🇬": "BG",
    "🇨🇦": "CA", "🇨🇳": "CN", "🇭🇷": "HR", "🇨🇺": "CU", "🇨🇾": "CY",
    "🇨🇿": "CZ", "🇩👑": "DK", "🇪🇬": "EG", "🇪🇪": "EE", "🇫🇮": "FI",
    "🇫🇷": "FR", "🇬🇪": "GE", "🇩🇪": "DE", "🇬🇷": "GR", "🇭🇰": "HK",
    "🇭🇺": "HU", "🇮🇸": "IS", "🇮🇳": "IN", "🇮🇩": "ID", "🇮🇷": "IR",
    "🇮🇶": "IQ", "🇮🇪": "IE", "🇮🇱": "IL", "🇮🇹": "IT", "🇯🇵": "JP",
    "🇰🇿": "KZ", "🇰🇪": "KE", "🇰🇼": "KW", "🇰🇬": "KG", "🇱🇻": "LV",
    "🇱🇧": "LB", "🇱🇾": "LY", "🇱🇹": "LT", "🇱🇺": "LU", "🇲🇾": "MY",
    "🇲🇽": "MX", "🇲🇩": "MD", "🇲🇳": "MN", "🇲🇪": "ME", "🇲🇦": "MA",
    "🇳🇱": "NL", "🇳🇿": "NZ", "🇳🇬": "NG", "🇰🇵": "KP", "🇳🇴": "NO",
    "🇵稳": "PK", "🇵🇸": "PS", "🇵🇪": "PE", "🇵🇭": "PH", "🇵🇱": "PL",
    "🇵🇹": "PT", "🇶🇦": "QA", "🇷🇴": "RO", "🇷🇺": "RU", "🇸🇦": "SA",
    "🇷🇸": "RS", "🇸🇬": "SG", "🇸🇰": "SK", "🇸🇮": "SI", "🇿🇦": "ZA",
    "🇰🇷": "KR", "🇪🇸": "ES", "🇸🇪": "SE", "🇨🇭": "CH", "🇹🇼": "TW",
    "🇹🇯": "TJ", "🇹🇭": "TH", "🇹🇷": "TR", "🇹🇲": "TM", "🇺🇦": "UA",
    "🇦🇪": "AE", "🇬🇧": "GB", "🇺🇸": "US", "🇺🇾": "UY", "🇺🇿": "UZ",
    "🇻🇳": "VN",
}

COUNTRY_NAMES = {
    "россия": "RU", "russia": "RU", "russian": "RU", "ru": "RU",
    "германия": "DE", "germany": "DE", "deutschland": "DE", "de": "DE",
    "франция": "FR", "france": "FR", "fr": "FR",
    "сша": "US", "usa": "US", "united states": "US", "us": "US",
    "нидерланды": "NL", "netherlands": "NL", "holland": "NL", "nl": "NL",
    "великобритания": "GB", "uk": "GB", "united kingdom": "GB", "gb": "GB",
    "украина": "UA", "ukraine": "UA", "ua": "UA",
    "польша": "PL", "poland": "PL", "pl": "PL",
    "канада": "CA", "canada": "CA", "ca": "CA",
    "италия": "IT", "italy": "IT", "it": "IT",
    "испания": "ES", "spain": "ES", "es": "ES",
    "швеция": "SE", "sweden": "SE", "se": "SE",
    "норвегия": "NO", "norway": "NO", "no": "NO",
    "финляндия": "FI", "finland": "FI", "fi": "FI",
    "дания": "DK", "denmark": "DK", "dk": "DK",
    "швейцария": "CH", "switzerland": "CH", "ch": "CH",
    "австрия": "AT", "austria": "AT", "at": "AT",
    "бельгия": "BE", "belgium": "BE", "be": "BE",
    "япония": "JP", "japan": "JP", "jp": "JP",
    "южная корея": "KR", "south korea": "KR", "korea": "KR", "kr": "KR",
    "сингапур": "SG", "singapore": "SG", "sg": "SG",
    "индия": "IN", "india": "IN", "in": "IN",
    "бразилия": "BR", "brazil": "BR", "br": "BR",
    "турция": "TR", "turkey": "TR", "türkiye": "TR", "tr": "TR",
    "израиль": "IL", "israel": "IL", "il": "IL",
    "оаэ": "AE", "uae": "AE", "arab emirates": "AE", "ae": "AE",
    "китай": "CN", "china": "CN", "cn": "CN",
    "гонконг": "HK", "hong kong": "HK", "hk": "HK",
    "австралия": "AU", "australia": "AU", "au": "AU",
    "казахстан": "KZ", "kazakhstan": "KZ", "kz": "KZ",
    "латвия": "LV", "latvia": "LV", "lv": "LV",
    "литва": "LT", "lithuania": "LT", "lt": "LT",
    "эстония": "EE", "estonia": "EE", "ee": "EE",
    "чехия": "CZ", "czech": "CZ", "czechia": "CZ", "cz": "CZ",
    "словакия": "SK", "slovakia": "SK", "sk": "SK",
    "венгрия": "HU", "hungary": "HU", "hu": "HU",
    "румыния": "RO", "romania": "RO", "ro": "RO",
    "болгария": "BG", "bulgaria": "BG", "bg": "BG",
    "греция": "GR", "greece": "GR", "gr": "GR",
    "португалия": "PT", "portugal": "PT", "pt": "PT",
    "мексика": "MX", "mexico": "MX", "mx": "MX",
    "аргентина": "AR", "argentina": "AR", "ar": "AR",
    "чили": "CL", "chile": "CL", "cl": "CL",
    "египет": "EG", "egypt": "EG", "eg": "EG",
    "юар": "ZA", "south africa": "ZA", "za": "ZA",
    "сербия": "RS", "serbia": "RS", "rs": "RS",
    "хорватия": "HR", "croatia": "HR", "hr": "HR",
    "словения": "SI", "slovenia": "SI", "si": "SI",
    "люксембург": "LU", "luxembourg": "LU", "lu": "LU",
    "кипр": "CY", "cyprus": "CY", "cy": "CY",
    "мальта": "MT", "malta": "MT", "mt": "MT",
    "исландия": "IS", "iceland": "IS", "is": "IS",
    "монако": "MC", "monaco": "MC", "mc": "MC",
    "лихтенштейн": "LI", "liechtenstein": "LI", "li": "LI",
    "андорра": "AD", "andorra": "AD", "ad": "AD",
}

CODE_TO_RU = {
    "AF": "Афганистан", "AL": "Албания", "DZ": "Алжир", "AD": "Андорра", "AO": "Ангола",
    "AR": "Аргентина", "AM": "Армения", "AU": "Австралия", "AT": "Австрия", "AZ": "Азербайджан",
    "BD": "Бангладеш", "BY": "Беларусь", "BE": "Бельгия", "BR": "Бразилия", "BG": "Болгария",
    "CA": "Канада", "CN": "Китай", "HR": "Хорватия", "CU": "Куба", "CY": "Кипр",
    "CZ": "Чехия", "DK": "Дания", "EG": "Египет", "EE": "Эстония", "FI": "Финляндия",
    "FR": "Франция", "GE": "Грузия", "DE": "Германия", "GR": "Греция", "HK": "Гонконг",
    "HU": "Венгрия", "IS": "Исландия", "IN": "Индия", "ID": "Индонезия", "IR": "Иран",
    "IQ": "Ирак", "IE": "Ирландия", "IL": "Израиль", "IT": "Италия", "JP": "Япония",
    "KZ": "Казахстан", "KE": "Кения", "KW": "Кувейт", "KG": "Киргизия", "LV": "Латвия",
    "LB": "Ливан", "LY": "Ливия", "LT": "Литва", "LU": "Люксембург", "MY": "Малайзия",
    "MX": "Мексика", "MD": "Молдова", "MN": "Монголия", "ME": "Черногория", "MA": "Марокко",
    "NL": "Нидерланды", "NZ": "Новая Зеландия", "NG": "Нигерия", "KP": "Северная Корея", "NO": "Норвегия",
    "PK": "Пакистан", "PS": "Палестина", "PE": "Перу", "PH": "Филиппины", "PL": "Польша",
    "PT": "Португалия", "QA": "Катар", "RO": "Румыния", "RU": "Россия", "SA": "Саудовская Аравия",
    "RS": "Сербия", "SG": "Сингапур", "SK": "Словакия", "SI": "Словения", "ZA": "ЮАР",
    "KR": "Южная Корея", "ES": "Испания", "SE": "Швеция", "CH": "Швейцария", "TW": "Тайвань",
    "TJ": "Таджикистан", "TH": "Таиланд", "TR": "Турция", "TM": "Туркменистан", "UA": "Украина",
    "AE": "ОАЭ", "GB": "Великобритания", "US": "США", "UY": "Уругвай", "UZ": "Узбекистан",
    "VN": "Вьетнам",
}

def code_to_flag(code):
    if len(code) != 2:
        return ""
    return chr(ord(code[0]) + 0x1F1E6 - ord('A')) + chr(ord(code[1]) + 0x1F1E6 - ord('A'))

def ip_in_cidr(ip_str, cidr_str):
    try:
        return ipaddress.ip_address(ip_str) in ipaddress.ip_network(cidr_str, strict=False)
    except ValueError:
        return False

def is_ip_allowed(ip_str):
    if not ALLOWED_CIDRS:
        return True
    return any(ip_in_cidr(ip_str, cidr) for cidr in ALLOWED_CIDRS)

def extract_sni(url, comment):
    parsed = urlparse(url)
    qs = parse_qs(parsed.query)
    if 'sni' in qs:
        return qs['sni'][0]
    if parsed.hostname:
        try:
            ipaddress.ip_address(parsed.hostname)
        except ValueError:
            return parsed.hostname
    return ""

def is_whitelisted_sni(sni):
    if not WHITELISTED_SNI:
        return True
    return sni in WHITELISTED_SNI

def extract_ip_from_url(url):
    parsed = urlparse(url)
    host = parsed.hostname
    if host:
        try:
            ipaddress.ip_address(host)
            return host
        except ValueError:
            return None
    return None

def extract_flag_and_country(comment):
    flag_match = re.findall(r'[\U0001F1E6-\U0001F1FF]{2}', comment)
    if flag_match:
        flag_emoji = flag_match[0]
        if flag_emoji in FLAG_TO_CODE:
            code = FLAG_TO_CODE[flag_emoji]
            return flag_emoji, CODE_TO_RU.get(code, "🌐 Не определено")

    code_match = re.search(r'\b([A-Z]{2})\b', comment)
    if code_match:
        code = code_match.group(1).upper()
        if code in CODE_TO_RU:
            return code_to_flag(code), CODE_TO_RU[code]

    text_lower = comment.lower()
    for name, code in COUNTRY_NAMES.items():
        if name in text_lower:
            return code_to_flag(code), CODE_TO_RU.get(code, "🌐 Не определено")

    return "", "🌐 Не определено"

def parse_config_line(line):
    line = line.strip()
    if not line:
        return None

    url_part, comment = "", ""
    if '#' in line:
        url_part, comment = line.split('#', 1)
        url_part = url_part.strip()
        comment = comment.strip()
    else:
        url_part = line

    if not any(url_part.startswith(p) for p in ('vless://', 'vmess://', 'trojan://', 'ss://')):
        return None

    flag, country = extract_flag_and_country(comment + ' ' + url_part)
    sni = extract_sni(url_part, comment)
    if not is_whitelisted_sni(sni):
        return None

    ip = extract_ip_from_url(url_part)
    if ip and not is_ip_allowed(ip):
        return None

    new_name = f"{flag} {country} | SNI: {sni} | 🌴ЯлтаВПН".strip()
    return {
        "base_url": url_part,
        "new_name": new_name,
        "flag": flag,
        "country": country,
        "sni": sni,
        "ip": ip
    }

def fetch_source(url):
    try:
        # Добавлен User-Agent для обхода потенциальных блокировок со стороны GitHub к "голым" скриптам
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code != 200:
            print(f"⚠️ {url} → статус {resp.status_code}")
            return []
        configs = []
        for line in resp.text.splitlines():
            parsed = parse_config_line(line)
            if parsed:
                configs.append(parsed)
        return configs
    except Exception as e:
        print(f"❌ Ошибка {url}: {e}")
        return []

def save_to_drive(content, filename):
    path = os.path.join(BASE_DIR, filename)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

def log_to_sheet(total, cidr_count, unique_sni):
    path = os.path.join(BASE_DIR, LOG_FILE)
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    needed_header = not os.path.exists(path)
    with open(path, 'a', encoding='utf-8') as f:
        if needed_header:
            f.write("timestamp,total,cidr_count,unique_sni\n")
        f.write(f"{now},{total},{cidr_count},{unique_sni}\n")

def main():
    all_configs = []
    url_set = set()

    print(f"🌴 Ingushetiya - python ВПН | лимит: {LIMIT} | источников: {len(SOURCES)}")
    print("📡 Начало параллельной загрузки источников...")

    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_url = {executor.submit(fetch_source, url): url for url in SOURCES}
        
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                configs = future.result()
                for cfg in configs:
                    if cfg['base_url'] not in url_set:
                        url_set.add(cfg['base_url'])
                        all_configs.append(cfg)
            except Exception as e:
                print(f"❌ Ошибка обработки пула для {url}: {e}")

    all_configs = all_configs[:LIMIT]

    now = datetime.now()
    timestamp = now.strftime('%Y-%m-%d %H:%M:%S')
    cidr_count = sum(1 for c in all_configs if c['ip'] and is_ip_allowed(c['ip']))
    unique_sni = len({c['sni'] for c in all_configs})

    # Исправлены разорванные многострочные f-строки
    if IS_PUBLIC:
        announce = (f"🌴 Ingushetiya - python ВПН | "
                    f"конфигов: {len(all_configs)} (CIDR: {cidr_count}) | SNI: {unique_sni} | "
                    f"обновлено: {timestamp}")
    else:
        announce = (f"🌴 Ingushetiya - python ВПН 🔒PRIVATE | "
                    f"конфигов: {len(all_configs)} (CIDR: {cidr_count}) | SNI: {unique_sni} | "
                    f"обновлено: {timestamp}")

    header = [
        "#profile-update-interval: 1",
        "#support-url: https://t.me/YaltaVPN_Obxod",
        f"#profile-title: {announce}",
        "#hide-settings: 1",
        ""
    ]

    content = '\n'.join(header)
    for cfg in all_configs:
        content += cfg['base_url'] + '#' + cfg['new_name'] + '\n'

    save_to_drive(content, CONFIG_FILE)
    log_to_sheet(len(all_configs), cidr_count, unique_sni)

    print(f"✅ Успешно сохранено {len(all_configs)} конфигов.")
    print(f"📁 Результаты сохранены в корень: {BASE_DIR}")

if __name__ == "__main__":
    main()
