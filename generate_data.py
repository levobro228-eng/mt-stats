import json
import os
import time
import urllib.request
import urllib.parse
from datetime import datetime

VEHICLES_JSON_URL = 'https://raw.githubusercontent.com/nickelc/wot-vehicles-data/master/vehicles.json'
CLICKHOUSE_URL = 'http://db.wotstat.info:80/?user=public'

TYPE_MAP = {
    'lightTank': 'LT',
    'mediumTank': 'MT',
    'heavyTank': 'HT',
    'AT-SPG': 'AT',
    'SPG': 'SPG'
}

TYPE_MAP_RU = {
    'LT': 'LT',
    'MT': 'MT',
    'HT': 'HT',
    'AT': 'AT',
    'SPG': 'SPG'
}

def load_vehicles_database():
    print("Loading vehicles database...")
    try:
        req = urllib.request.Request(
            VEHICLES_JSON_URL,
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))
        tank_db = {}
        for item in data:
            tag = item.get('tag', '')
            if tag:
                tank_db[tag] = {
                    'is_premium': item.get('is_premium', False)
                }
        print("Loaded " + str(len(tank_db)) + " tanks")
        return tank_db
    except Exception as e:
        print("Error: " + str(e))
        return {}

def classify_tank(tag, tank_db):
    if tag in tank_db:
        if tank_db[tag].get('is_premium', False):
            return 'premium'
        return 'regular'
    return 'collector'

def build_query(months, min_battles):
    q = "SELECT e.tankTag, t.nameRU, t.shortNameRU, t.nation, t.iconUrl, e.level, e.type, e.total_battles, e.wins, e.win_rate FROM (SELECT tankTag, tankLevel AS level, tankType AS type, count() AS total_battles, countIf(result = 'win') AS wins, round(wins * 100.0 / total_battles, 2) AS win_rate FROM Event_OnBattleResult WHERE battleMode = 'REGULAR' AND region = 'RU' AND dateTime >= now() - INTERVAL "
    q += str(months)
    q += " MONTH AND tankTag NOT LIKE '%_Gold%' AND tankTag NOT LIKE '%_Prem%' AND tankTag NOT LIKE '%_MK%' AND tankTag NOT LIKE '%_Patton%' AND tankTag NOT LIKE '%_prot%' AND tankTag NOT LIKE '%_CFE_%' AND tankTag NOT LIKE '%_3D%' AND tankTag NOT LIKE '%_Beijing_Opera%' AND tankTag NOT LIKE '%_QL%' AND tankTag NOT LIKE '%_CN%' AND tankTag NOT LIKE '%_CO%' AND tankTag NOT LIKE '%_DV%' AND tankTag NOT LIKE '%_BF%' AND tankTag NOT LIKE '%_GrandFinal%' AND tankTag NOT LIKE '%_FL%' AND tankTag NOT LIKE '%_SH%' AND tankTag NOT LIKE '%_WT24_%' AND tankTag NOT LIKE '%_IC4_%' AND tankTag NOT LIKE '%_Ziqiang%' AND tankTag NOT LIKE '%_Yong_Bing%' AND tankTag NOT LIKE '%_Yongshi%' AND tankTag NOT LIKE '%_T' GROUP BY tankTag, tankLevel, tankType HAVING total_battles > "
    q += str(min_battles)
    q += ") e LEFT JOIN TankList t ON e.tankTag = t.tag WHERE t.nameRU IS NOT NULL AND t.nameRU != '' ORDER BY e.level ASC, e.type ASC, e.win_rate DESC"
    return q

def fetch_stats(months, max_retries=3):
    min_battles = 300 if months <= 6 else 1000
    query = build_query(months, min_battles)
    
    for attempt in range(max_retries):
        try:
            print("Attempt " + str(attempt + 1) + "/" + str(max_retries))
            url = CLICKHOUSE_URL + "&query=" + urllib.parse.quote(query)
            req = urllib.request.Request(
                url,
                method='GET',
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            with urllib.request.urlopen(req, timeout=60) as response:
                text = response.read().decode('utf-8')
            
            lines = text.strip().split('\n')
            tanks = []
            for line in lines:
                if not line.strip():
                    continue
                parts = line.split('\t')
                if len(parts) >= 10:
                    tag = parts[0]
                    name = parts[1]
                    short_name = parts[2]
                    nation = parts[3]
                    icon_url = parts[4]
                    level = parts[5]
                    tank_type = parts[6]
                    battles = parts[7]
                    wins = parts[8]
                    win_rate = parts[9]
                    
                    if not name or not name.strip():
                        continue
                    
                    tank = {}
                    tank['tag'] = tag
                    tank['name'] = name
                    tank['short_name'] = short_name
                    tank['nation'] = nation.lower() if nation else 'unknown'
                    tank['icon'] = icon_url if icon_url else ''
                    tank['level'] = int(level)
                    tank['type'] = TYPE_MAP.get(tank_type, tank_type)
                    tank['type_code'] = tank_type
                    tank['battles'] = int(battles)
                    tank['wins'] = int(wins)
                    tank['win_rate'] = float(win_rate)
                    tanks.append(tank)
            return tanks
        except Exception as e:
            print("Error: " + str(e))
            if attempt < max_retries - 1:
                print("Waiting 5 seconds...")
                time.sleep(5)
    raise Exception("Failed after " + str(max_retries) + " attempts")

def main():
    print("Starting data generation...")
    os.makedirs('data', exist_ok=True)
    
    tank_db = load_vehicles_database()
    
    data = {}
    data['updated'] = datetime.now().strftime('%d.%m.%Y %H:%M')
    data['periods'] = {}
    
    periods = [('3m', 3), ('6m', 6), ('12m', 12), ('all', 999)]
    
    for key, months in periods:
        print("Loading " + str(months) + " months...")
        tanks = fetch_stats(months)
        
        for tank in tanks:
            tank['category'] = classify_tank(tank['tag'], tank_db)
        
        data['periods'][key] = tanks
        print("Got " + str(len(tanks)) + " tanks")
    
    with open('data/tanks.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    total = sum(len(v) for v in data['periods'].values())
    print("Done! Saved " + str(total) + " records")

if __name__ == '__main__':
    main()
