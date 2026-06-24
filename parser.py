import requests
import re
import time
from urllib.parse import urlparse

# ============ ТВОИ ИСТОЧНИКИ ============
SOURCES = [
    "https://raw.githubusercontent.com/arshiafarrokhi/v2ray-config/main/splitted/link1.txt",
    "https://raw.githubusercontent.com/arshiafarrokhi/v2ray-config/main/splitted/link2.txt",
    "https://raw.githubusercontent.com/arshiafarrokhi/v2ray-config/main/splitted/link3.txt",
    "https://raw.githubusercontent.com/arshiafarrokhi/v2ray-config/main/splitted/link4.txt",
    "https://raw.githubusercontent.com/arshiafarrokhi/v2ray-config/main/splitted/link5.txt",
    "https://raw.githubusercontent.com/arshiafarrokhi/v2ray-config/main/splitted/link6.txt",
    "https://raw.githubusercontent.com/hawshemi/ipScraper/main/configs/all_configs.txt",
    "https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/configs/configs.txt",
    "https://raw.githubusercontent.com/peyman-ps/ConfigCollector/main/result/configs.txt",
      # эту лучше удалить или закомментировать
]

# ============ ПАРСИНГ ОДНОЙ СТРОКИ ============
def parse_config_line(line):
    """Из строки вырезает первую ссылку с известным протоколом"""
    line = line.strip()
    if not line:
        return None

    # Все протоколы в одном месте, опечатки исправлены
    protocols = [
        'vless://', 'vmess://', 'trojan://', 
        'ss://', 'ssr://', 'hysteria2://', 'hy2://'
    ]

    for proto in protocols:
        if line.startswith(proto):
            return line
        idx = line.find(proto)
        if idx != -1:
            # обрезаем всё после пробела, если есть
            end = line.find(' ', idx)
            if end == -1:
                end = len(line)
            return line[idx:end]
    return None

# ============ ЗАГРУЗКА ИСТОЧНИКА ============
def fetch_source(url):
    """Скачивает содержимое по ссылке, возвращает список строк"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        resp = requests.get(url, timeout=30, headers=headers)
        resp.encoding = 'utf-8'
        if resp.status_code == 200:
            return resp.text.splitlines()
        else:
            print(f"❌ Ошибка {resp.status_code} при загрузке {url}")
            return []
    except Exception as e:
        print(f"⚠️ Исключение при загрузке {url}: {e}")
        return []

# ============ ГЛАВНАЯ ФУНКЦИЯ ============
def main():
    all_configs = []   # сюда собираем все найденные конфиги

    for url in SOURCES:
        print(f"🔄 Обрабатываю: {url}")
        lines = fetch_source(url)
        if not lines:
            continue

        for line in lines:
            cfg = parse_config_line(line)
            if cfg:
                all_configs.append(cfg)
        time.sleep(0.5)  # маленькая пауза между источниками

    # ======== УБИРАЕМ ДУБЛИКАТЫ (вот здесь, родной!) ========
    unique_configs = list(dict.fromkeys(all_configs))
    print(f"🧹 Было {len(all_configs)} строк, осталось {len(unique_configs)} уникальных")

    # ======== СОХРАНЯЕМ В ФАЙЛ ========
    with open('ING007internet', 'w', encoding='utf-8') as f:
        for cfg in unique_configs:
            f.write(cfg + '\n')

    print("✅ Готово! Файл ING007internet обновлён.")

if __name__ == "__main__":
    main()
