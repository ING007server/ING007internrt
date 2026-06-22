import os
import re
import ipaddress
import requests
from datetime import datetime
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
    SOURCES.append(f"https://raw.githubusercontent.com/AvenCores/goida-vpn-configs/refs/heads/main/githubmirror/{i}.txt")

# ===================== НАСТРОЙКИ =====================
LIMIT = 3000
CONFIG_FILE = "YaltaVPN - Subscription"
LOG_FILE = "log.csv"

# ===================== СТРАНЫ =====================
FLAG_TO_CODE = {
    "🇦🇫": "AF", "🇦🇱": "AL", "🇩🇿": "DZ", "🇦🇩": "AD", "🇦🇴": "AO",
    "🇦🇷": "AR", "🇦🇲": "AM", "🇦🇺": "AU", "🇦🇹": "AT", "🇦🇿": "AZ",
    "🇧🇩": "BD", "🇧🇾": "BY", "🇧🇪": "BE", "🇧🇷": "BR", "🇧🇬": "BG",
    "🇨🇦": "CA", "🇨🇳": "CN", "🇭🇷": "HR", "🇨🇺": "CU", "🇨🇾": "CY",
    "🇨🇿": "CZ", "🇩🇰": "DK", "🇪🇬": "EG", "🇪🇪": "EE", "🇫🇮": "FI",
    "🇫🇷": "FR", "🇬🇪": "GE", "🇩🇪": "DE", "🇬🇷": "GR", "🇭🇰": "HK",
    "🇭🇺": "HU", "🇮🇸": "IS", "🇮🇳": "IN", "🇮🇩": "ID", "🇮🇷": "IR",
    "🇮🇶": "IQ", "🇮🇪": "IE", "🇮🇱": "IL", "🇮🇹": "IT", "🇯🇵": "JP",
    "🇰🇿": "KZ", "🇰🇪": "KE", "🇰🇼": "KW", "🇰🇬": "KG", "🇱🇻": "LV",
    "🇱🇧": "LB", "🇱🇾": "LY", "🇱🇹": "LT", "🇱🇺": "LU", "🇲🇾": "MY",
    "🇲🇽": "MX", "🇲🇩": "MD", "🇲🇳": "MN", "🇲🇪": "ME", "🇲🇦": "MA",
    "🇳🇱": "NL", "🇳🇿": "NZ", "🇳🇬": "NG", "🇰🇵": "KP", "🇳🇴": "NO",
    "🇵🇰": "PK", "🇵🇸": "PS", "🇵🇪": "PE", "🇵🇭": "PH", "🇵🇱": "PL",
    "🇵🇹": "PT", "🇶🇦": "QA", "🇷🇴": "RO", "🇷🇺": "RU", "🇸🇦": "SA",
    "🇷🇸": "RS", "🇸🇬": "SG", "🇸🇰": "SK", "🇸🇮": "SI", "🇿🇦": "ZA",
    "🇰🇷": "KR", "🇪🇸": "ES", "🇸🇪": "SE", "🇨🇭": "CH", "🇹🇼": "TW",
    "🇹🇯": "TJ", "🇹🇭": "TH", "🇹🇷": "TR", "🇹🇲": "TM", "🇺🇦": "UA",
    "🇦🇪": "AE", "🇬🇧": "GB", "🇺🇸": "US", "🇺🇾": "UY", "🇺🇿": "UZ",
    "🇻🇳": "VN",
}

# ===================== ОСНОВНЫЕ ФУНКЦИИ =====================
def fetch_source(url):
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        lines = resp.text.splitlines()
        configs = []
        for line in lines:
            cfg = parse_config_line(line.strip())
            if cfg:
                configs.append(cfg)
        return configs
    except Exception as e:
        print(f"Ошибка загрузки {url}: {e}")
        return []

def parse_config_line(line):
    if not line or line.startswith('#') or len(line) < 10:
        return None
    try:
        if line.startswith('vless://') or line.startswith('vmess://') or line.startswith('trojan://'):
            base = line.split('#')[0].strip()
            return {"base_url": base}
    except:
        pass
    return None

def save_to_drive(content, filename):
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Файл {filename} сохранён ({len(content)} символов)")
    except Exception as e:
        print(f"❌ Ошибка сохранения {filename}: {e}")

def log_to_sheet(total, success, failed):
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(f"{timestamp},{total},{success},{failed}\n")
        print(f"📋 Лог обновлён: {total} конфигов")
    except:
        pass

def main():
    print("🚀 Запуск парсера YaltaVPN...")
    all_configs = []
    
    with ThreadPoolExecutor(max_workers=12) as executor:
        future_to_url = {executor.submit(fetch_source, url): url for url in SOURCES}
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                configs = future.result()
                all_configs.extend(configs)
                print(f"✅ {url} → +{len(configs)} конфигов")
            except Exception as e:
                print(f"❌ {url} → ошибка: {e}")

    # Убираем дубликаты
    seen = set()
    unique_configs = [c for c in all_configs if not (c["base_url"] in seen or seen.add(c["base_url"]))]

    unique_configs = unique_configs[:LIMIT]
    print(f"📊 Итого уникальных: {len(unique_configs)} (лимит {LIMIT})")

    if not unique_configs:
        print("⚠️ Конфигов не найдено!")
        return

    subscription = "\n".join(cfg["base_url"] for cfg in unique_configs)
    
    save_to_drive(subscription, CONFIG_FILE)
    log_to_sheet(len(unique_configs), len(unique_configs), 0)

    print(f"🎉 Готово! Файлы созданы.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"💥 Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
