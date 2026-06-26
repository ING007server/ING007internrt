#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Парсер конфигов VPN с опциональной фильтрацией по сроку годности.
Поддерживает vless, trojan, ss (параметр expires/exp в query).
Для vmess фильтрация не применяется (слишком сложно).
"""

import requests
import time
import re
import base64
import argparse
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse, parse_qs
import socket
from datetime import datetime

# ======================== НАСТРОЙКИ ========================
DEFAULT_SOURCES = [
    "https://raw.githubusercontent.com/flaafix/AetrisVPN-white-list-lite/refs/heads/main/AetrisVPN.txt",
    "https://raw.githubusercontent.com/WSJuJuB01/WS_Parser/refs/heads/main/subscription.txt",
    "https://raw.githubusercontent.com/zieng2/wl/main/vless_universal.txt",
    "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/WHITE-CIDR-RU-checked.txt",
    "https://raw.githubusercontent.com/btsk161/Freeinternet_byMygalaru.github.io/refs/heads/main/premium.txt",
]

PROTOCOLS = ['vless', 'vmess', 'trojan', 'ss', 'ssr', 'hysteria2', 'hy2']
LINK_PATTERN = re.compile(
    r'(?:^|[\s"\'<>])(' + '|'.join(PROTOCOLS) + r')://[^\s"\'<>]+',
    re.IGNORECASE
)

# ======================== ЛОГГЕР ========================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('error.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ======================== ЗАГРУЗКА ИСТОЧНИКА ========================
def fetch_source(url, timeout=30, retries=3, session=None):
    if session is None:
        session = requests.Session()
    for attempt in range(1, retries + 1):
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            resp = session.get(url, timeout=timeout, headers=headers)
            resp.encoding = resp.apparent_encoding or 'utf-8'
            if resp.status_code == 200:
                return resp.text.splitlines()
            else:
                logger.warning(f"HTTP {resp.status_code} при загрузке {url} (попытка {attempt})")
        except Exception as e:
            logger.warning(f"Ошибка загрузки {url} (попытка {attempt}): {e}")
        time.sleep(2 ** attempt)
    logger.error(f"Не удалось загрузить {url} после {retries} попыток")
    return []

# ======================== ПАРСИНГ ССЫЛОК ========================
def extract_links(lines):
    links = []
    for line in lines:
        if not line.strip():
            continue
        for m in LINK_PATTERN.finditer(line):
            links.append(m.group(1))
    return links

# ======================== ФИЛЬТР ПО СРОКУ (опционально) ========================
def is_expired(link):
    """
    Проверяет, истёк ли срок у ссылки (если есть параметр expires/exp).
    Поддерживает vless, trojan, ss (с query-параметрами).
    Для vmess возвращает False (не проверяем).
    """
    # Разбираем URL
    parsed = urlparse(link)
    scheme = parsed.scheme.lower()
    
    # Для vmess – пропускаем (сложно парсить внутри base64)
    if scheme == 'vmess':
        return False
    
    # Получаем параметры из query
    query_params = parse_qs(parsed.query)
    # Ищем ключи: expires, exp
    expire_str = None
    for key in ['expires', 'exp']:
        if key in query_params:
            expire_str = query_params[key][0]
            break
    
    if not expire_str:
        return False  # нет срока – считаем валидным
    
    # Пробуем преобразовать в int (Unix timestamp в секундах)
    try:
        expire_ts = int(expire_str)
        # Если число слишком большое (10 цифр) – это секунды; если 13 – миллисекунды
        if expire_ts > 10**12:  # миллисекунды
            expire_ts = expire_ts // 1000
        now = int(time.time())
        return expire_ts < now
    except ValueError:
        # Может быть в формате ISO? Игнорируем, считаем валидным
        return False

def filter_expired(links):
    """Возвращает список ссылок, у которых срок не истёк"""
    valid = []
    expired_count = 0
    for link in links:
        if is_expired(link):
            expired_count += 1
        else:
            valid.append(link)
    if expired_count:
        logger.info(f"⏳ Отсеяно по сроку годности: {expired_count} ссылок")
    return valid

# ======================== TCP-ПРОВЕРКА ========================
def check_tcp(link, timeout=3):
    try:
        parsed = urlparse(link)
        host = parsed.hostname
        port = parsed.port or (443 if parsed.scheme in ['vless', 'vmess', 'trojan'] else 80)
        if not host:
            return False
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False

# ======================== ОСНОВНАЯ ФУНКЦИЯ ========================
def main():
    parser = argparse.ArgumentParser(description='Парсинг конфигов VPN')
    parser.add_argument('--sources', '-s', nargs='*', help='Список URL (если не указаны, берутся стандартные)')
    parser.add_argument('--output', '-o', default='configs_all.txt', help='Файл для сырых ссылок')
    parser.add_argument('--check', '-c', action='store_true', help='Проверять доступность TCP (замедляет работу)')
    parser.add_argument('--expire', '-e', action='store_true', help='Фильтровать ссылки с истекшим сроком (expires/exp)')
    parser.add_argument('--timeout', '-t', type=int, default=30, help='Таймаут загрузки (сек)')
    parser.add_argument('--retries', '-r', type=int, default=3, help='Количество повторных попыток')
    parser.add_argument('--threads', '-j', type=int, default=10, help='Количество потоков для загрузки')
    args = parser.parse_args()

    sources = args.sources if args.sources else DEFAULT_SOURCES
    logger.info(f"Запуск парсера. Источников: {len(sources)}")
    start_time = datetime.now()

    # Загружаем все источники параллельно
    all_lines = []
    with ThreadPoolExecutor(max_workers=args.threads) as executor:
        future_to_url = {
            executor.submit(fetch_source, url, args.timeout, args.retries): url
            for url in sources
        }
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                lines = future.result()
                if lines:
                    all_lines.extend(lines)
                    logger.info(f"✅ Загружено {len(lines)} строк из {url}")
                else:
                    logger.warning(f"⚠️ Нет данных из {url}")
            except Exception as e:
                logger.error(f"❌ Ошибка обработки {url}: {e}")

    # Парсим ссылки
    raw_links = extract_links(all_lines) if all_lines else []
    logger.info(f"🎯 Извлечено ссылок (до удаления дублей): {len(raw_links)}")

    # Убираем дубликаты
    seen = set()
    unique_links = []
    for link in raw_links:
        if link not in seen:
            seen.add(link)
            unique_links.append(link)
    logger.info(f"🧹 Уникальных ссылок: {len(unique_links)}")

    # Фильтр по сроку (если включён)
    if args.expire and unique_links:
        unique_links = filter_expired(unique_links)
        logger.info(f"🧾 После фильтрации по сроку: {len(unique_links)} ссылок")

    # Опциональная TCP-проверка
    if args.check and unique_links:
        logger.info("🔍 Проверка доступности TCP (может занять время)...")
        alive = [link for link in unique_links if check_tcp(link)]
        logger.info(f"✅ Прошло проверку: {len(alive)} из {len(unique_links)}")
        unique_links = alive

    # Если конфигов нет – создаём пустой файл с предупреждением
    if not unique_links:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write("# ⚠️ Конфиги не найдены! Проверь источники.\n")
        logger.warning("❌ Конфиги не найдены. Выходной файл пуст.")
        return

    # --- СОХРАНЕНИЕ ---
    with open(args.output, 'w', encoding='utf-8') as f:
        for link in unique_links:
            f.write(link + '\n')
    logger.info(f"✅ Сырые ссылки сохранены в {args.output}")

    # Base64-подписка
    b64_data = base64.b64encode('\n'.join(unique_links).encode()).decode()
    sub_file = 'sub_base64.txt'
    with open(sub_file, 'w', encoding='utf-8') as f:
        f.write(b64_data)
    logger.info(f"✅ Base64-подписка сохранена в {sub_file}")

    # Разделение по протоколам
    proto_files = {proto: [] for proto in PROTOCOLS}
    for link in unique_links:
        for proto in PROTOCOLS:
            if link.startswith(proto + '://'):
                proto_files[proto].append(link)
                break

    for proto, links_list in proto_files.items():
        if links_list:
            filename = f"{proto}.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                for link in links_list:
                    f.write(link + '\n')
            logger.info(f"✅ {len(links_list)} конфигов {proto} сохранено в {filename}")

    elapsed = datetime.now() - start_time
    logger.info(f"🎉 Готово! Затрачено времени: {elapsed.total_seconds():.2f} сек.")

if __name__ == "__main__":
    main()
