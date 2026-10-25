import json
import os
import time
import urllib.request
import urllib.parse
from datetime import datetime

# URL открытого справочника танков с GitHub
VEHICLES_JSON_URL = 'https://raw.githubusercontent.com/nickelc/wot-vehicles-data/master/vehicles.json'

CLICKHOUSE_URL = 'http://db.wotstat.info:80/?user=public'

TYPE_MAP = {'lightTank': 'ЛТ', 'mediumTank': 'СТ', 'heavyTank': 'ТТ', 'AT-SPG': 'ПТ-САУ', 'SPG': 'САУ'}

def load_vehicles_database():
    """Загружает базу данных танков из открытого источника"""
    print("Загрузка базы данных танков...")
    try:
        req = urllib.request.Request(VEHICLES_JSON_URL, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))
        
        # Создаём словарь: tag -> {is_premium, type}
        tank_db = {}
        for item in data:
            tag = item.get('tag', '')
            if tag:
                tank_db[tag] = {
                    'is_premium': item.get('is_premium', False),
                    'type': item.get('type', '')
                }
        
        print(f"  Загружено {len(tank_db)} танков из справочника")
        return tank_db
    except Exception as e:
        print(f"  Ошибка загрузки справочника: {e}")
        print("  Используем резервный метод классификации")
        return {}

def classify_tank(tag, tank_db):
    """Определяет тип танка по справочнику"""
    if tag in tank_db:
        info = tank_db[tag]
        if info['is_premium']:
            return 'premium'
        return 'regular'
    
    # Если танка нет в справочнике — проверяем по паттернам в теге
    if any(suffix in tag for suffix in ['_Gold', '_Prem', '_MK', '_Patton']):
        return 'premium'
    
    # Если ничего не подошло — считаем коллекционным
    return 'collector'

def fetch_stats(months, max_retries=3):
    """Получает статистику боёв из wotstat"""
    min_battles = 300 if months <= 6 else 1000
    
    query = f"""
    SELECT 
        e.tankTag,
        t.nameRU AS tank_name,
        t.shortNameRU AS short_name,
        t.nation,
        t.iconUrl,
        e.level,
        e.type,
        e.total_battles,
        e.wins,
        e.win_rate
    FROM (
        SELECT 
            tankTag,
            tankLevel AS level,
            tankType AS type,
            count() AS total_battles,
            countIf(result = 'win') AS wins,
            round(wins * 100.0 / total_battles, 2) AS win_rate
        FROM Event_OnBattleResult
        WHERE battleMode = 'REGULAR'
          AND region = 'RU'
