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
    "🇵🇰": "PK",   # ← ИСПРАВИЛ
    # ... остальное без изменений
}

# (оставь весь остальной код FLAG_TO_CODE, COUNTRY_NAMES, CODE_TO_RU как был)

def main():
    print("🚀 Запуск парсера YaltaVPN...")
    all_configs = []
    
    with ThreadPoolExecutor(max_workers=15) as executor:
        future_to_url = {executor.submit(fetch_source, url): url for url in SOURCES}
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                configs = future.result()
                all_configs.extend(configs)
                print(f"✅ {url} → +{len(configs)} конфигов")
            except Exception as e:
                print(f"❌ {url} → ошибка: {e}")

    # Убираем дубли
    seen = set()
    unique_configs = []
    for c in all_configs:
        if c["base_url"] not in seen:
            seen.add(c["base_url"])
            unique_configs.append(c)

    unique_configs = unique_configs[:LIMIT]
    print(f"📊 Итого уникальных конфигов: {len(unique_configs)} (лимит {LIMIT})")

    if not unique_configs:
        print("⚠️ Не найдено ни одного валидного конфига!")
        return

    # Формируем подписку
    subscription = "\n".join(cfg["base_url"] for cfg in unique_configs)
    
    # Сохраняем
    save_to_drive(subscription, CONFIG_FILE)
    log_to_sheet(len(unique_configs), 0, 0)   # упрощённо

    print(f"✅ Файлы успешно сохранены: {CONFIG_FILE} и {LOG_FILE}")

# ===================== ОСТАЛЬНЫЕ ФУНКЦИИ =====================
# (вставь сюда все остальные функции из твоего текущего parser.py: fetch_source, save_to_drive, log_to_sheet, parse_config_line и т.д.)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"💥 Критическая ошибка в main(): {e}")
        import traceback
        traceback.print_exc()
