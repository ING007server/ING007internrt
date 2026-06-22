import os
import re
import requests
from datetime import datetime

# Имя выходного файла (должно совпадать с file_pattern в blank.yml)
CONFIG_FILE = "ING007internet"

# Список источников (URL или локальные файлы)
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

def parse_config_line(line):
    """Извлекает конфиг из строки, если она содержит vless://, vmess://, trojan:// и т.д."""
    line = line.strip()
    if not line:
        return None
    # Ищем протоколы
    protocols = ['vless://', 'vmess://', 'trojan://', 'ss://', 'ssr://']
    for proto in protocols:
        if line.startswith(proto):
            return line
    # Если строка содержит ссылку где-то внутри (например, после текста)
    for proto in protocols:
        if proto in line:
            # Берём подстроку от протокола до конца или до пробела
            idx = line.find(proto)
            end = line.find(' ', idx)
            if end == -1:
                return line[idx:]
            else:
                return line[idx:end]
    return None

def fetch_configs():
    """Собирает конфиги из всех источников."""
    configs = []
    for url in SOURCES:
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                for line in resp.text.splitlines():
                    conf = parse_config_line(line)
                    if conf:
                        configs.append(conf)
            else:
                print(f"⚠️ Не удалось получить {url} (код {resp.status_code})")
        except Exception as e:
            print(f"❌ Ошибка при загрузке {url}: {e}")
    return configs

def save_configs(configs):
    """Сохраняет конфиги в файл."""
    if not configs:
        print("⚠️ Конфигов не найдено! Файл создан не будет.")
        return False
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        for conf in configs:
            f.write(conf + '\n')
    print(f"✅ Сохранено {len(configs)} конфигов в {CONFIG_FILE}")
    return True

if __name__ == "__main__":
    print("🚀 Запуск парсера...")
    configs = fetch_configs()
    if save_configs(configs):
        print("📁 Файл создан:", CONFIG_FILE)
        # Покажем содержимое для отладки
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                content = f.read()
                print("📄 Первые 200 символов:\n", content[:200])
        else:
            print("❌ Файл НЕ создан! Проверьте права доступа.")
    else:
        print("❌ Парсер завершился без создания файла.")
