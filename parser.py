import requests
import time
from urllib.parse import urlparse

# ============ ТВОИ ИСТОЧНИКИ ============
SOURCES = [
    "https://raw.githubusercontent.com/ING007server/ING007internrt/refs/heads/main/ING007internet",
    "https://vpn.tgflovv.ru:8000/free-white/54af9268-49c4-422b-ac39-c34447a7ea04",
    "https://vpn.tgflovv.ru:8000/free-white-ru/54af9268-49c4-422b-ac39-c34447a7ea04",
]

# ============ ПАРСИНГ ОДНОЙ СТРОКИ ============
def parse_config_line(line):
    """Из строки вырезает первую ссылку с известным протоколом"""
    line = line.strip()
    if not line:
        return None

    protocols = [
        'vless://', 'vmess://', 'trojan://',
        'ss://', 'ssr://', 'hysteria2://', 'hy2://'
    ]

    for proto in protocols:
        if line.startswith(proto):
            return line
        idx = line.find(proto)
        if idx != -1:
            end = line.find(' ', idx)
            if end == -1:
                end = len(line)
            return line[idx:end]
    return None

# ============ ЗАГРУЗКА ИСТОЧНИКА С ПОВТОРАМИ ============
def fetch_source(url, retries=3):
    """Скачивает содержимое с повторами при ошибках"""
    for attempt in range(1, retries + 1):
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            resp = requests.get(url, timeout=45, headers=headers)
            resp.encoding = 'utf-8'
            if resp.status_code == 200:
                lines = resp.text.splitlines()
                print(f"   ✅ Загружено {len(lines)} строк")
                return lines
            else:
                print(f"   ⚠️ Попытка {attempt}: HTTP {resp.status_code}")
                if attempt == retries:
                    print(f"   ❌ Ошибка {resp.status_code} после {retries} попыток")
                    return []
        except Exception as e:
            print(f"   ⚠️ Попытка {attempt}: {e}")
            if attempt == retries:
                print(f"   ❌ Исключение после {retries} попыток")
                return []
        time.sleep(2)  # пауза между попытками
    return []

# ============ ГЛАВНАЯ ФУНКЦИЯ ============
def main():
    all_configs = []
    total_sources = len(SOURCES)

    print(f"🚀 Запуск парсера. Источников: {total_sources}\n")

    for idx, url in enumerate(SOURCES, 1):
        print(f"[{idx}/{total_sources}] 🔄 Обрабатываю: {url}")
        lines = fetch_source(url)
        if not lines:
            print(f"   ⏭️ Пропускаю (нет данных)")
            continue

        found = 0
        for line in lines:
            cfg = parse_config_line(line)
            if cfg:
                all_configs.append(cfg)
                found += 1
        print(f"   🎯 Найдено конфигов в этом источнике: {found}")
        time.sleep(0.5)  # пауза между источниками

    # Убираем дубликаты
    unique_configs = list(dict.fromkeys(all_configs))
    print(f"\n🧹 Итого: {len(all_configs)} строк, уникальных: {len(unique_configs)}")

    # Сохраняем в файл
    if not unique_configs:
        with open('ING007internet', 'w', encoding='utf-8') as f:
            f.write("# ⚠️ Конфиги не найдены! Проверь доступность источников.\n")
        print("❌ Файл создан, но он пуст (нет конфигов).")
    else:
        with open('ING007internet', 'w', encoding='utf-8') as f:
            for cfg in unique_configs:
                f.write(cfg + '\n')
        print(f"✅ Готово! {len(unique_configs)} уникальных конфигов записано в ING007internet.")

if __name__ == "__main__":
    main()
