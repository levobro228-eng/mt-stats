import json
import os
import time
import urllib.request
import urllib.parse
from datetime import datetime

VEHICLES_JSON_URL = 'https://raw.githubusercontent.com/nickelc/wot-vehicles-data/master/vehicles.json'
CLICKHOUSE_URL = 'http://db.wotstat.info:80/?user=public'

TYPE_MAP = {
    'lightTank': 'ЛТ',
    'mediumTank': 'СТ',
    'heavyTank': 'ТТ',
    'AT-SPG': 'ПТ-САУ',
    'SPG': 'САУ'
}

PREMIUM_SUFFIXES = ['_Gold', '_Prem', '_MK', '_Patton', '_prot', '_CFE_', '_3D', '_Beijing_Opera', '_QL', '_CN', '_CO', '_DV', '_BF', '_GrandFinal', '_FL', '_SH', '_WT24_', '_IC4_', '_Ziqiang', '_Yong_Bing', '_Yongshi']

def load_vehicles_database():
    print("Загрузка базы данных танков...")
    try:
        req = urllib.request.Request(VEHICLES_JSON_URL, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))
        tank_db = {}
        for item in data:
            tag = item.get('tag', '')
            if tag:
                tank_db[tag] = {
                    'is_premium': item.get('is_premium', False),
                    'type': item.get('type', '')
                }
        print("  Загружено " + str(len(tank_db)) + " танков из справочника")
        return tank_db
    except Exception as e:
        print("  Ошибка загрузки справочника: " + str(e))
        return {}

def classify_tank(tag, tank_db):
    if tag in tank_db:
        info = tank_db[tag]
        if info.get('is_premium', False):
            return 'premium'
        return 'regular'
    for suffix in PREMIUM_SUFFIXES:
        if suffix in tag:
            return 'premium'
    return 'collector'

def build_query(months, min_battles):
    parts = []
    parts.append("SELECT e.tankTag, t.nameRU AS tank_name, t.shortNameRU AS short_name, t.nation, t.iconUrl, e.level, e.type, e.total_battles, e.wins, e.win_rate")
    parts.append("FROM (")
    parts.append("SELECT tankTag, tankLevel AS level, tankType AS type, count() AS total_battles, countIf(result = 'win') AS wins, round(wins * 100.0 / total_battles, 2) AS win_rate")
    parts.append("FROM Event_OnBattleResult")
    parts.append("WHERE battleMode = 'REGULAR'")
    parts.append("AND region = 'RU'")
    parts.append("AND dateTime >= now() - INTERVAL " + str(months) + " MONTH")
    
    exclude_tags = ['_Gold', '_Prem', '_MK', '_Patton', '_prot', '_CFE_', '_3D', '_Beijing_Opera', '_QL', '_CN', '_CO', '_DV', '_BF', '_GrandFinal', '_FL', '_SH', '_WT24_', '_IC4_', '_Ziqiang', '_Yong_Bing', '_Yongshi', '_T']
    for tag in exclude_tags:
        parts.append("AND tankTag NOT LIKE '%" + tag + "%'")
    
    parts.append("GROUP BY tankTag, tankLevel, tankType")
    parts.append("HAVING total_battles > " + str(min_battles))
    parts.append(") e")
    parts.append("LEFT JOIN TankList t ON e.tankTag = t.tag")
    parts.append("WHERE t.nameRU IS NOT NULL AND t.nameRU != ''")
    parts.append("ORDER BY e.level ASC, e.type ASC, e
