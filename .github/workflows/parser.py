import os
import re
import requests
from datetime import datetime
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
CONFIG_FILE = "ING007interrnet"
LOG_FILE = "log.csv"

# ===================== ОСНОВНЫЕ ФУНКЦИИ =====================
def fetch_source(url):
    try:
        resp = requests.get(url, timeout=20)
        resp.raise_for_status()
        lines = resp.text.splitlines()
        configs = []
        for line in lines:
            cfg = parse_config_line(line.strip())
            if cfg:
                configs.append(cfg)
        return configs
    except Exception as e:
        print(f"❌ Ошибка загрузки {url}: {e}")
        return []

def parse_config_line(line):
    line = line.strip()
    if not line or line.startswith('#') or len(line) < 30:
        return None
    
    try:
        # Более умный поиск — берём любую строку, где есть ссылка на протокол
        if any(proto in line for proto in ['vless://', 'vmess://', 'trojan://', 'ss://', 'ssr://', 'hysteria2://']):
            # Берём часть до первого # (или всю строку, если # нет)
            base = line.split('#')[0].strip()
            if any(base.startswith(proto) for proto in ['vless://', 'vmess://', 'trojan://', 'ss://', 'ssr://', 'hysteria2://']):
                return {"base_url": base}
    except:
        pass
    return None

def save_to_drive(content, filename):
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ {filename} создан ({len(content)//1024} KB)")
    except Exception as e:
        print(f"❌ Ошибка сохранения {filename}: {e}")

def log_to_sheet(total, success, failed):
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(f"{timestamp},{total},{success},{failed}\n")
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
                print(f"✅ {url.split('/')[-1]} → +{len(configs)}")
            except Exception as e:
                print(f"❌ {url} → ошибка")

    # Убираем дубли
    seen = set()
    unique_configs = [c for c in all_configs if not (c["base_url"] in seen or seen.add(c["base_url"]))]
    unique_configs = unique_configs[:LIMIT]

    print(f"📊 Итого уникальных: {len(unique_configs)}")

    if not unique_configs:
        print("⚠️ Конфигов не найдено!")
        return

    subscription = "\n".join(c["base_url"] for c in unique_configs)
    
    save_to_drive(subscription, CONFIG_FILE)
    log_to_sheet(len(unique_configs), len(unique_configs), 0)

    print("🎉 Всё сохранено успешно!")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"💥 Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
