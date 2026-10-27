import json
import os
import time
import urllib.request
import urllib.parse
from datetime import datetime

DB_URL = 'http://db.wotstat.info:80/?user=public'
TANKOPEDIA_URL = 'https://tanki.su/api/tankopedia?realm=runet&language=ru'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

TYPE_MAP = {'lightTank': 'LT', 'mediumTank': 'MT', 'heavyTank': 'HT', 'AT-SPG': 'AT', 'SPG': 'SPG'}

def load_tankopedia():
    """Загружаем актуальный справочник техники из публичного API tanki.su"""
    print("Загрузка справочника техники из tanki.su...")
    try:
        req = urllib.request.Request(TANKOPEDIA_URL, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read().decode('utf-8'))
        
        catalog = {}
        tanks = data.get('data', {}).get('tanks', {})
        
        for tag, info in tanks.items():
            name = info.get('name', '').strip()
            if not name:
                continue
            
            nation = info.get('nation', 'unknown')
            tier = info.get('tier', 0)
            is_premium = info.get('is_premium', False)
            is_reward = info.get('is_reward', False)
            
            # Определяем категорию
            if is_reward:
                category = 'collector'
            elif is_premium:
                category = 'premium'
            else:
                category = 'regular'
            
            catalog[name.lower()] = {
                'nation': nation,
                'level': tier,
                'category': category
            }
        
        print("Загружено " + str(len(catalog)) + " танков из справочника")
        
        # Статистика
        levels = {}
        cats = {}
        for info in catalog.values():
            levels[info['level']] = levels.get(info['level'], 0) + 1
            cats[info['category']] = cats.get(info['category'], 0) + 1
        
        print("Уровни: " + str(sorted(levels.items())))
        print("Категории: " + str(cats))
        
        return catalog
    except Exception as e:
        print("Ошибка загрузки справочника: " + str(e))
        return {}

def classify_tank(name, catalog):
    key = name.strip().lower()
    if key in catalog:
        return catalog[key]
    return None

def build_query(months, min_b):
    parts = []
    parts.append("SELECT e.tankTag, t.nameRU, t.shortNameRU, t.nation, t.iconUrl, e.level, e.type, e.total_battles, e.wins, e.win_rate")
    parts.append("FROM (")
    parts.append("SELECT tankTag, tankLevel AS level, tankType AS type, count() AS total_battles, countIf(result = 'win') AS wins, round(wins * 100.0 / total_battles, 2) AS win_rate")
    parts.append("FROM Event_OnBattleResult")
    parts.append("WHERE battleMode = 'REGULAR'")
    parts.append("AND region = 'RU'")
    parts.append("AND dateTime >= now() - INTERVAL " + str(months) + " MONTH")
    
    exclude = ['_Gold', '_Prem', '_MK', '_Patton', '_prot', '_CFE_', '_3D', '_Beijing_Opera', '_QL', '_CN', '_CO', '_DV', '_BF', '_GrandFinal', '_FL', '_SH', '_WT24_', '_IC4_', '_Ziqiang', '_Yong_Bing', '_Yongshi']
    for tag in exclude:
        parts.append("AND tankTag NOT LIKE '%" + tag + "%'")
    
    parts.append("GROUP BY tankTag, tankLevel, tankType")
    parts.append("HAVING total_battles > " + str(min_b))
    parts.append(") e")
    parts.append("LEFT JOIN TankList t ON e.tankTag = t.tag")
    parts.append("WHERE t.nameRU IS NOT NULL AND t.nameRU != ''")
    parts.append("ORDER BY e.level ASC, e.type ASC, e.win_rate DESC")
    return "\n".join(parts)

def fetch(months, tries=3):
    min_b = 50
    query = build_query(months, min_b)
    for attempt in range(tries):
        try:
            print("Запрос статистики за " + str(months) + " мес. (попытка " + str(attempt + 1) + "/" + str(tries) + ")")
            url = DB_URL + "&query=" + urllib.parse.quote(query)
            req = urllib.request.Request(url, method='GET', headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=120) as r:
                text = r.read().decode('utf-8')
            lines = text.strip().split('\n')
            tanks = []
            for line in lines:
                if not line.strip():
                    continue
                parts = line.split('\t')
                if len(parts) >= 10:
                    tag, name, short, nation, icon, level, ttype, battles, wins, wr = parts[:10]
                    if not name or not name.strip():
                        continue
                    tanks.append({
                        'tag': tag,
                        'name': name,
                        'short_name': short,
                        'nation': nation.lower() if nation else 'unknown',
                        'icon': icon if icon else '',
                        'level': int(level),
                        'type': TYPE_MAP.get(ttype, ttype),
                        'type_code': ttype,
                        'battles': int(battles),
                        'wins': int(wins),
                        'win_rate': float(wr)
                    })
            return tanks
        except Exception as e:
            print("Ошибка: " + str(e))
            if attempt < tries - 1:
                print("Ожидание 5 сек...")
                time.sleep(5)
    raise Exception("Не удалось получить данные после " + str(tries) + " попыток")

def main():
    print("=" * 50)
    print("Запуск генерации данных")
    print("=" * 50)
    
    os.makedirs('data', exist_ok=True)
    
    # Шаг 1: Загружаем справочник из публичного API
    catalog = load_tankopedia()
    if not catalog:
        raise Exception("Не удалось загрузить справочник техники")
    
    data = {'updated': datetime.now().strftime('%d.%m.%Y %H:%M'), 'periods': {}}
    
    # Шаг 2: Для каждого периода получаем статистику боёв
    for key, months in [('3m', 3), ('6m', 6), ('12m', 12), ('all', 999)]:
        print("\nПериод: " + key + " (" + str(months) + " мес.)")
        tanks = fetch(months)
        
        matched = 0
        unmatched = 0
        for tank in tanks:
            info = classify_tank(tank['name'], catalog)
            if info:
                tank['category'] = info['category']
                tank['nation'] = info['nation']
                tank['level'] = info['level']
                matched += 1
            else:
                tank['category'] = 'regular'
                unmatched += 1
        
        print("  Получено: " + str(len(tanks)) + " танков")
        print("  Совпало со справочником: " + str(matched))
        print("  Не найдено в справочнике: " + str(unmatched))
        
        data['periods'][key] = tanks
    
    # Шаг 3: Сохраняем
    with open('data/tanks.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    total = sum(len(v) for v in data['periods'].values())
    print("\n" + "=" * 50)
    print("Готово! Сохранено " + str(total) + " записей")
    print("=" * 50)

if __name__ == '__main__':
    main()
