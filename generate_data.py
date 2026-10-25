import json
import os
import time
import urllib.request
import urllib.parse
from datetime import datetime

VEHICLES_URL = 'https://raw.githubusercontent.com/nickelc/wot-vehicles-data/master/vehicles.json'
DB_URL = 'http://db.wotstat.info:80/?user=public'

TYPE_MAP = {'lightTank': 'LT', 'mediumTank': 'MT', 'heavyTank': 'HT', 'AT-SPG': 'AT', 'SPG': 'SPG'}

def load_db():
    print("Loading vehicles...")
    try:
        req = urllib.request.Request(VEHICLES_URL, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read().decode('utf-8'))
        db = {}
        for item in data:
            tag = item.get('tag', '')
            if tag:
                db[tag] = {'premium': item.get('is_premium', False)}
        print("Loaded " + str(len(db)) + " tanks")
        return db
    except Exception as e:
        print("Error: " + str(e))
        return {}

def classify(tag, db):
    if tag in db:
        return 'premium' if db[tag].get('premium', False) else 'regular'
    return 'collector'

def build_query(months, min_b):
    q = "SELECT e.tankTag, t.nameRU, t.shortNameRU, t.nation, t.iconUrl, e.level, e.type, e.total_battles, e.wins, e.win_rate FROM (SELECT tankTag, tankLevel AS level, tankType AS type, count() AS total_battles, countIf(result = 'win') AS wins, round(wins * 100.0 / total_battles, 2) AS win_rate FROM Event_OnBattleResult WHERE battleMode = 'REGULAR' AND region = 'RU' AND dateTime >= now() - INTERVAL "
    q += str(months)
    q += " MONTH AND tankTag NOT LIKE '%_Gold%' AND tankTag NOT LIKE '%_Prem%' AND tankTag NOT LIKE '%_MK%' AND tankTag NOT LIKE '%_Patton%' AND tankTag NOT LIKE '%_prot%' AND tankTag NOT LIKE '%_CFE_%' AND tankTag NOT LIKE '%_3D%' AND tankTag NOT LIKE '%_Beijing_Opera%' AND tankTag NOT LIKE '%_QL%' AND tankTag NOT LIKE '%_CN%' AND tankTag NOT LIKE '%_CO%' AND tankTag NOT LIKE '%_DV%' AND tankTag NOT LIKE '%_BF%' AND tankTag NOT LIKE '%_GrandFinal%' AND tankTag NOT LIKE '%_FL%' AND tankTag NOT LIKE '%_SH%' AND tankTag NOT LIKE '%_WT24_%' AND tankTag NOT LIKE '%_IC4_%' AND tankTag NOT LIKE '%_Ziqiang%' AND tankTag NOT LIKE '%_Yong_Bing%' AND tankTag NOT LIKE '%_Yongshi%' AND tankTag NOT LIKE '%_T' GROUP BY tankTag, tankLevel, tankType HAVING total_battles > "
    q += str(min_b)
    q += ") e LEFT JOIN TankList t ON e.tankTag = t.tag WHERE t.nameRU IS NOT NULL AND t.nameRU != '' ORDER BY e.level ASC, e.type ASC, e.win_rate DESC"
    return q

def fetch(months, tries=3):
    min_b = 300 if months <= 6 else 1000
    query = build_query(months, min_b)
    for attempt in range(tries):
        try:
            print("Attempt " + str(attempt + 1) + "/" + str(tries))
            url = DB_URL + "&query=" + urllib.parse.quote(query)
            req = urllib.request.Request(url, method='GET', headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=60) as r:
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
            print("Error: " + str(e))
            if attempt < tries - 1:
                print("Waiting...")
                time.sleep(5)
    raise Exception("Failed after " + str(tries) + " attempts")

def main():
    print("Starting...")
    os.makedirs('data', exist_ok=True)
    db = load_db()
    data = {'updated': datetime.now().strftime('%d.%m.%Y %H:%M'), 'periods': {}}
    for key, months in [('3m', 3), ('6m', 6), ('12m', 12), ('all', 999)]:
        print("Loading " + str(months) + " months...")
        tanks = fetch(months)
        for tank in tanks:
            tank['category'] = classify(tank['tag'], db)
        data['periods'][key] = tanks
        print("Got " + str(len(tanks)) + " tanks")
    with open('data/tanks.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    total = sum(len(v) for v in data['periods'].values())
    print("Done! Saved " + str(total) + " records")

if __name__ == '__main__':
    main()
