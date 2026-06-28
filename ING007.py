#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import time
import re
import os
import csv
from datetime import datetime
from urllib.parse import urlparse, parse_qs, unquote
from collections import defaultdict
import ipaddress
import logging

# ======================== НАСТРОЙКИ ========================
IS_PUBLIC = False                 # True - публичная подписка, False - приватная
MAX_CONFIGS = 1000
CONFIG_FILE = 'configs_ING007.txt'
VERSION_FILE = 'version_ING007.txt'
STATS_CSV = 'stats_ING007.csv'
LOG_FILE = 'log_ING007.txt'

ENABLE_SNI_CHECK = False
ENABLE_PRIORITY_IGAREK = True
ENABLE_RENAME_CONFIGS = True

# ======================== БЕЛЫЕ СПИСКИ (ОСТАВЛЕНЫ БЕЗ ИЗМЕНЕНИЙ) ========================
WHITELIST_DOMAINS = [
    'gosuslugi.ru', 'mos.ru', 'nalog.ru', 'zakupki.gov.ru', 'kremlin.ru',
    'government.ru', 'gd.ru', 'genproc.gov.ru', 'mvd.ru', 'mchs.ru',
    'rostrud.gov.ru', 'ach.gov.ru', 'rsv.ru', 'mintrud.gov.ru', 'minfin.gov.ru',
    'council.gov.ru', 'ksrf.ru', 'scrf.gov.ru', 'mid.ru', 'minobrnauki.gov.ru',
    'minzdrav.gov.ru', 'minsport.gov.ru', 'minstroyrf.ru', 'mintrans.gov.ru',
    'minpromtorg.gov.ru', 'digital.gov.ru', 'roskomnadzor.ru', 'mirpay.ru',
    'mironline.ru', 'sbp.nspk.ru', 'sberbank.ru', 'tbank.ru', 'alfabank.ru',
    'vtb.ru', 'psbank.ru', 'gazprombank.ru', 'open.ru', 'rshb.ru', 'mkb.ru',
    'absolutbank.ru', 'sovcombank.ru', 'bankuralsib.ru', 'raiffeisen.ru',
    'citibank.ru', 'unicreditbank.ru', 'rosbank.ru', 'beeline.ru', 'megafon.ru',
    'mts.ru', 'rt.ru', 't2.ru', 'sbermobile.ru', 'tmobile.ru', 'ertelecom.ru',
    'domru.ru', 'ttk.ru', 'rostelecom.ru', 'tinkoff.ru', 'yota.ru', 'vk.com',
    'ok.ru', 'mail.ru', 'yandex.ru', 'dzen.ru', 'rutube.ru', 'max.ru',
    'vkvideo.ru', 'sferum.ru', 'disk.yandex.ru', '360.yandex.ru', 'kinopoisk.ru',
    'ivi.ru', 'hh.ru', 'pikabu.ru', 'ozon.ru', 'wildberries.ru', 'avito.ru',
    'megamarket.ru', 'sbermegamarket.ru', 'magnit.ru', 'vkusvill.ru', 'dixy.ru',
    'detmir.ru', 'vkusnoitochka.ru', 'burgerking.ru', 'kfc.ru', 'cdek.ru',
    'samokat.ru', 'kuper.ru', 'gsev.ru', 'utkonos.ru', 'sbermarket.ru',
    'lenta.com', 'perekrestok.ru', '5ka.ru', 'metro-cc.ru', 'ashan.ru',
    'spar.ru', 'petrovich.ru', 'dns-shop.ru', 'drom.ru', 'apteka.ru',
    'rbc.ru', 'gazeta.ru', 'lenta.ru', 'rambler.ru', 'kp.ru', 'ria.ru',
    'iz.ru', 'tass.ru', 'kommersant.ru', 'vedomosti.ru', 'mk.ru', 'rg.ru',
    'ntv.ru', '1tv.ru', 'rt.ru', 'tnt-online.ru', 'ctc.ru', 'matchtv.ru',
    'zvezdanews.ru', 'vmeste-rf.tv', 'aif.ru', 'pnp.ru', 'vesti.ru',
    'russia.tv', 'tvzvezda.ru', 'ren.tv', '5-tv.ru', 'domashniy.ru',
    'muz-tv.ru', 'otr-online.ru', 'tvcenter.ru', 'tv3.ru', 'spastv.ru',
    '2gis.ru', 'russianhighways.ru', 'rzd.ru', 'tutu.ru', 'maxim.taxi',
    'gismeteo.ru', 'aeroflot.ru', 'pobeda.aero', 's7.ru', 'utair.ru',
    'grandservis.ru', 'citydrive.ru', 'obr.ru', 'edu.ru', 'ege.edu.ru',
    'school.ru', 'moodle.ru', 'itmo.ru', 'bmstu.ru', 'spbu.ru', 'msu.ru',
    'mipt.ru', 'hse.ru', 'ranepa.ru', 'mgimo.ru', 'urfu.ru', 'kpfu.ru',
    'nntu.ru', 'tpu.ru', 'susu.ru', 'donstu.ru', 'sfedu.ru', 'job.ru',
    'rabota.ru', 'superjob.ru', 'zarplata.ru', 'sberid.ru', 'goskey.ru',
    'chestnyznak.ru', 'sbis.ru', 'diadoc.ru', 'pfr.gov.ru', 'fss.ru',
    'cmcsmd.ru', 'banki.ru', 'm.gosuslugi.ru', 'kaspersky.ru', 'drweb.ru',
    'tensor.ru', 'kontur.ru', 'evotor.ru'
]

ALLOWED_CIDRS = [
    '5.255.255.0/24', '77.88.0.0/18', '87.250.250.0/24', '95.108.0.0/16',
    '217.69.128.0/20', '109.120.128.0/17', '185.30.164.0/22', '91.200.120.0/24',
    '193.232.96.0/24', '92.223.80.0/22', '178.248.0.0/21'
]

# ======================== ИСТОЧНИКИ (ТЕ ЖЕ) ========================
ALL_SOURCES = [
    "https://raw.githubusercontent.com/SER38Off/happ-subscription/refs/heads/main/sub1-white-lists.txt",
    "https://raw.githubusercontent.com/SER38Off/happ-subscription/refs/heads/main/sub2-white-lists.txt",
    "https://raw.githubusercontent.com/SER38Off/happ-subscription/refs/heads/main/BEST-sub3-white-lists.txt",
    "https://raw.githubusercontent.com/SER38Off/happ-subscription/refs/heads/main/white-sub1.txt",
    "https://raw.githubusercontent.com/SER38Off/happ-subscription/refs/heads/main/white-sub11.txt",
    "https://raw.githubusercontent.com/SER38Off/happ-subscription/refs/heads/main/white-sub12.txt",
    "https://raw.githubusercontent.com/SER38Off/happ-subscription/refs/heads/main/white-sub13.txt",
    "https://raw.githubusercontent.com/SER38Off/happ-subscription/refs/heads/main/white-sub14.txt",
    "https://raw.githubusercontent.com/SER38Off/happ-subscription/refs/heads/main/white-sub15.txt",
    "https://raw.githubusercontent.com/SER38Off/happ-subscription/refs/heads/main/white-sub2.txt",
    "https://raw.githubusercontent.com/SER38Off/happ-subscription/refs/heads/main/white-sub3.txt",
    "https://raw.githubusercontent.com/SER38Off/happ-subscription/refs/heads/main/white-sub4.txt",
    "https://raw.githubusercontent.com/SER38Off/happ-subscription/refs/heads/main/white-sub5.txt",
    "https://raw.githubusercontent.com/SER38Off/happ-subscription/refs/heads/main/white-sub6.txt",
    "https://raw.githubusercontent.com/SER38Off/happ-subscription/refs/heads/main/all-white-sub.txt",
    "https://raw.githubusercontent.com/SER38Off/happ-subscription/refs/heads/main/all-white-lists-servers.txt",
    "https://raw.githubusercontent.com/SER38Off/happ-subscription/refs/heads/main/best-white-lists-russia.txt",
    "https://raw.githubusercontent.com/SER38Off/happ-subscription/refs/heads/main/russia-white-lists.txt",
    "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/WHITE-CIDR-RU-checked.txt",
    "https://raw.githubusercontent.com/AvenCores/goida-vpn-configs/refs/heads/main/githubmirror/1.txt",
    "https://raw.githubusercontent.com/dequar/deqwl/refs/heads/main/deray.txt",
    "https://sub.cisvpn.xyz/FFT4xcGGwo8k7e9s",
    "https://raw.githubusercontent.com/v0id9/vpn-configs/refs/heads/main/vpn.txt",
    "https://gist.github.com/lsncococososo-rgb/3bee1c3aa943e0019708292aaa5f5fde/raw/ef3bf5892faa2d01ef98892449b5813c8a5ac487/GRN_VPN",
    "https://vspsub.onrender.com/get/6fkgjw",
    "https://vspsub.onrender.com/get/6auai",
    "https://raw.githubusercontent.com/raponchik/EcstasyVPN/refs/heads/main/ne%20dlya%20prodazhi",
    "https://gitverse.ru/api/repos/vansfenix/vansFenix/raw/branch/master/WildVFmini",
    "https://raw.githubusercontent.com/dmitriistekolnikov/Free_vpns_for_Russ/refs/heads/main/Vip.txt",
    "https://raw.githubusercontent.com/dmitriistekolnikov/Free_vpns_for_Russ/refs/heads/main/YouTube.txt",
    "https://raw.githubusercontent.com/ChkavHalyavaVPN/Chkav-HalyavaVPNUS-vpn-duo/refs/heads/main/vpn.txt",
    "https://gist.githubusercontent.com/HalyavusVPNUS/a93def732d3c624029c09c393dd0772e/raw/afaa5733c4b9d573195cfb2af21030e2cb5c1ae3/%25D0%25BA%25D0%25BE%25D0%25BD%25D1%2584%25D0%25B8%25D0%25B3%25D0%25B8",
    "https://base44.app/api/apps/6a142ae2965f19733954fc09/files/mp/public/6a142ae2965f19733954fc09/bd1b875de_subscription.txt",
    "https://gist.githubusercontent.com/j80547013-max/6abf8d9a407a9338ec82fc0754beeb99/raw/01890ab4a2fe739c77f1d45495d30ed80a15ab15/gistfile1.txt",
    "https://yax.nenadoblokirowatgnidda.ru/exec?url=http%3A%2F%2F77.110.104.181%3A5002%2Fsub%2FdGd0ZnRnLDE3ODA1ODc4MTI4fdXFeLwfA",
    "https://vspsub.onrender.com/get/88tzen",
    "https://109.237.98.81:2096/kvn/7qpy5bx22ejc4d5i",
    "https://gist.githubusercontent.com/moksim76/19e5c747b19f9ab4610609bcde01fb3d/raw/5d9ac6883ceb0a9e2e94040defabb8b97c1f317d/XuexVpn%2520Free",
    "https://bostvpn.duckdns.org:2096/YVH2bhbw2324w/i3cau11f8qfx49su",
    "https://vspsub.onrender.com/get/5xxuhj",
    "https://vpn.zotus.ru/sub.php",
    "https://tinyurl.com/WIFISUBAERYX",
    "https://tinyurl.com/SUBLTEAERYX",
    "https://gist.githubusercontent.com/zorka-project/efc486572e465d9fb6698264e9895f59/raw/kuertov-project.txt?nocache=1",
    "https://vspsub.onrender.com/get/n6bhp",
    "https://script.google.com/macros/s/AKfycby6bSt2cNMil43ZIv0sHwXUnEHfMqN2hbjGETfPG1m_iwjkO_ih_yp6pXt-NVc48_6w/exec?url=https://mix-macros.alexanderoff.ru/mixed/@vlessrus/?url=http://65.109.221.193:44321/20260608_114432_vpn.txt"
]

# ======================== ПРИОРИТЕТ ИСТОЧНИКОВ ========================
sources_to_use = list(ALL_SOURCES)
if ENABLE_PRIORITY_IGAREK:
    igarek_sources = ["https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/WHITE-CIDR-RU-checked.txt"]
    sources_to_use = [s for s in sources_to_use if s not in igarek_sources]
    sources_to_use = igarek_sources + sources_to_use

for i in range(2, 21):
    sources_to_use.append(f"https://raw.githubusercontent.com/AvenCores/goida-vpn-configs/refs/heads/main/githubmirror/{i}.txt")

# ======================== СТРАНЫ И ФЛАГИ ========================
COUNTRY_MAP = {
    '🇺🇸': 'США',
    '🇬🇧': 'Великобритания',
    '🇩🇪': 'Германия',
    '🇫🇷': 'Франция',
    '🇫🇮': 'Финляндия',
    '🇳🇱': 'Нидерланды',
    '🇷🇺': 'Россия',
    '🇨🇳': 'Китай'
}
URL_FLAG_MAP = {
    '%F0%9F%87%BA%F0%9F%87%B8': '🇺🇸',
    '%F0%9F%87%AC%F0%9F%87%A7': '🇬🇧',
    '%F0%9F%87%A9%F0%9F%87%AA': '🇩🇪',
    '%F0%9F%87%AB%F0%9F%87%B7': '🇫🇷',
    '%F0%9F%87%AB%F0%9F%87%AE': '🇫🇮',
    '%F0%9F%87%B3%F0%9F%87%B1': '🇳🇱',
    '%F0%9F%87%B7%F0%9F%87%BA': '🇷🇺',
    '%F0%9F%87%A8%F0%9F%87%B3': '🇨🇳'
}
TEXT_COUNTRY_MAP = {
    'us': '🇺🇸', 'usa': '🇺🇸',
    'uk': '🇬🇧',
    'de': '🇩🇪',
    'fr': '🇫🇷',
    'fi': '🇫🇮',
    'nl': '🇳🇱',
    'ru': '🇷🇺',
    'cn': '🇨🇳'
}

# ======================== ЛОГГЕР ========================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler(LOG_FILE, encoding='utf-8'), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# ======================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ========================
def extract_flag_and_country(text):
    if not text:
        return {'flag': '🌐', 'country': 'Anycast'}
    for encoded, flag in URL_FLAG_MAP.items():
        if encoded in text:
            return {'flag': flag, 'country': COUNTRY_MAP.get(flag, 'Anycast')}
    import re
    emoji_pattern = re.compile('[\U0001F1E6-\U0001F1FF]{2}', flags=re.UNICODE)
    match = emoji_pattern.search(text)
    if match:
        flag = match.group()
        return {'flag': flag, 'country': COUNTRY_MAP.get(flag, 'Anycast')}
    lower = text.lower()
    for code, flag in TEXT_COUNTRY_MAP.items():
        if code in lower:
            return {'flag': flag, 'country': COUNTRY_MAP.get(flag, code.upper())}
    return {'flag': '🌐', 'country': 'Anycast'}

def extract_sni(url_part, comment):
    full = url_part + '#' + comment
    sni = None
    sni_match = re.search(r'[?&]sni=([^&]+)', full)
    if sni_match:
        sni = unquote(sni_match.group(1))
    if not sni and comment:
        host_match = re.search(r'host[=:]\s*([^\s,]+)', comment, re.I)
        if host_match:
            sni = host_match.group(1)
    return sni

def extract_ip_from_url(url_part):
    try:
        match = re.search(r'@([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+):', url_part)
        if match:
            return match.group(1)
        match = re.search(r'([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+):[0-9]+', url_part)
        if match:
            return match.group(1)
        return None
    except:
        return None

def is_ip_in_cidr(ip, cidr):
    try:
        return ipaddress.ip_address(ip) in ipaddress.ip_network(cidr, strict=False)
    except:
        return False

def is_whitelisted_ip(ip):
    if not ip:
        return False
    for cidr in ALLOWED_CIDRS:
        if is_ip_in_cidr(ip, cidr):
            return True
    return False

def is_whitelisted_sni(sni):
    if not ENABLE_SNI_CHECK or not sni:
        return False
    sni_lower = sni.lower()
    for domain in WHITELIST_DOMAINS:
        if sni_lower == domain or sni_lower.endswith('.' + domain):
            return True
    return False

def get_next_version():
    if os.path.exists(VERSION_FILE):
        with open(VERSION_FILE, 'r') as f:
            try:
                return int(f.read().strip()) + 1
            except:
                return 1
    return 1

def save_version(version):
    with open(VERSION_FILE, 'w') as f:
        f.write(str(version))

def save_stats(stats):
    with open(STATS_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Тип', 'Значение', 'Количество'])
        for sni, count in stats.get('sni', {}).items():
            writer.writerow(['SNI', sni, count])
        for cidr, count in stats.get('cidr', {}).items():
            writer.writerow(['CIDR', cidr, count])

# ======================== ЗАГРУЗКА И ПАРСИНГ ========================
def fetch_source(url):
    try:
        logger.info(f"📥 {url[:70]}...")
        resp = requests.get(url, timeout=30, headers={'User-Agent': 'Mozilla/5.0'})
        if resp.status_code == 200:
            lines = resp.text.splitlines()
            return lines
        else:
            logger.warning(f"HTTP {resp.status_code} для {url}")
            return []
    except Exception as e:
        logger.error(f"Ошибка загрузки {url}: {e}")
        return []

def parse_config_line(line):
    line = line.strip()
    if not line:
        return None
    if '#' in line:
        url_part, comment = line.split('#', 1)
        url_part = url_part.strip()
        comment = comment.strip()
    else:
        url_part = line
        comment = ''
    if not url_part.startswith(('vless://', 'trojan://')):
        return None
    flag_info = extract_flag_and_country(comment + ' ' + url_part)
    flag = flag_info['flag']
    country = flag_info['country']
    sni = extract_sni(url_part, comment)
    if ENABLE_SNI_CHECK and sni and is_whitelisted_sni(sni):
        new_name = f"{flag} {country} | sni = {sni} | 🔥 от ING007" if ENABLE_RENAME_CONFIGS else (comment or f"{flag} {country}")
        return {'url': url_part, 'sni': sni, 'newName': new_name, 'source': 'sni', 'originalComment': comment}
    ip = extract_ip_from_url(url_part)
    if ip and is_whitelisted_ip(ip):
        new_name = f"{flag} {country} | ip = {ip} (CIDR) | 🔥 от ING007" if ENABLE_RENAME_CONFIGS else (comment or f"{flag} {country}")
        return {'url': url_part, 'sni': sni or 'no-sni', 'newName': new_name, 'source': 'cidr', 'originalComment': comment}
    return None

# ======================== MAIN ========================
def main():
    logger.info("🚀 ING007 VPN Parser v6.5 - SNI + CIDR")
    logger.info(f"🎯 Цель: {MAX_CONFIGS} конфигов")
    logger.info(f"📡 Всего источников: {len(sources_to_use)}")
    logger.info(f"⚙️ Настройки: SNI={'ВКЛ' if ENABLE_SNI_CHECK else 'ВЫКЛ'}, Приоритет Igarek={'ВКЛ' if ENABLE_PRIORITY_IGAREK else 'ВЫКЛ'}, Переименование={'ВКЛ' if ENABLE_RENAME_CONFIGS else 'ВЫКЛ'}")

    all_configs = []
    url_set = set()
    stats = {'sni': defaultdict(int), 'cidr': defaultdict(int)}

    for idx, url in enumerate(sources_to_use):
        if len(all_configs) >= MAX_CONFIGS:
            break
        lines = fetch_source(url)
        if not lines:
            continue
        for line in lines:
            if len(all_configs) >= MAX_CONFIGS:
                break
            cfg = parse_config_line(line)
            if cfg and cfg['url'] not in url_set:
                url_set.add(cfg['url'])
                all_configs.append(cfg)
                if cfg['source'] == 'sni':
                    stats['sni'][cfg['sni']] += 1
                else:
                    ip = extract_ip_from_url(cfg['url'])
                    if ip:
                        for cidr in ALLOWED_CIDRS:
                            if is_ip_in_cidr(ip, cidr):
                                stats['cidr'][cidr] += 1
                                break
        logger.info(f"📊 Прогресс: {len(all_configs)}/{MAX_CONFIGS}")

    version = get_next_version()
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    status = "Public" if IS_PUBLIC else "Private"
    header = [
        f"#profile-title: ING007 VPN ({status})",
        "#profile-update-interval: 12",
        f"#announce: Версия {version} | {len(all_configs)} конфигов | {timestamp}",
        "#hide-settings: 1",
        ""
    ]
    content = '\n'.join(header)

    for cfg in all_configs:
        if not ENABLE_RENAME_CONFIGS and cfg.get('originalComment'):
            content += f"{cfg['url']}#{cfg['originalComment']}\n"
        else:
            content += f"{cfg['url']}#{cfg['newName']}\n"

    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        f.write(content)

    save_version(version)
    save_stats(stats)

    logger.info(f"✅ ГОТОВО! Сохранено {len(all_configs)} конфигов. Версия: {version}")
    logger.info(f"🔹 SNI-конфигов: {sum(stats['sni'].values())}")
    logger.info(f"🔹 CIDR-конфигов: {sum(stats['cidr'].values())}")
    logger.info(f"🎯 Цель {MAX_CONFIGS} {'ДОСТИГНУТА ✅' if len(all_configs) >= MAX_CONFIGS else 'НЕ ДОСТИГНУТА ❌'}")

if __name__ == "__main__":
    main()
