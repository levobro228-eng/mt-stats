import json
import os
import time
import urllib.request
import urllib.parse
from datetime import datetime

DB_URL = 'http://db.wotstat.info:80/?user=public'

TYPE_MAP = {'lightTank': 'LT', 'mediumTank': 'MT', 'heavyTank': 'HT', 'AT-SPG': 'AT', 'SPG': 'SPG'}

# Суффиксы, которые указывают на премиумный танк
PREMIUM_SUFFIXES = [
    '_Gold', '_Prem', '_MK', '_Patton', '_prot', '_CFE_', '_3D',
    '_Beijing_Opera', '_QL', '_CN', '_CO', '_DV', '_BF',
    '_GrandFinal', '_FL', '_SH', '_WT24_', '_IC4_', '_Ziqiang',
    '_Yong_Bing', '_Yongshi'
]

# Известные коллекционные танки (по названиям)
COLLECTOR_NAMES = {
    'КВ-1С с МЗ', 'Объект 244', 'КВ-2 (Р)', 'Матильда IV',
    'К-2', 'ИС-2М', 'КВ-4 Креславского', 'Объект 252У',
    'КВ-220-2', 'Черчилль III', 'ИС-6', 'КВ-5',
    'Объект 252У Защитник', 'Сапсан', 'Защитник', 'Бизон',
    'EMIL 1951', 'Lowe', 'Кировец-1', 'Gonsalo', 'M6A2E1',
    'Charlemagne', 'WZ-111 model 6', 'BZ-176', 'Bisonte C45',
    'Caliban', 'Somua SM', 'Caernarvon Action X', 'Chrysler K',
    'Chrysler K GF', 'AMX M4 mle. 49', 'AMX M4 mle. 49 Liberte',
    'WZ-111 Alpine Tiger', 'VK 168.01 (P)', 'VK 168.01 Mauerbrecher',
    '112', 'FCM 50 t', 'Pudel', 'Cromwell B', 'M4A1 Revalorise',
    'Bretagne Panther', 'Sherman VC Firefly', 'Pz.Kpfw. IV Schmalturm',
    'AC 4 Experimental', 'M4A3E8 Fury', 'Chimera', 'Panzer 58 Mutz',
    'Primo Victoria', 'M48A2 Raumpnzer', 'CS-52 C', 'T26E3 Eagle 7',
    'Panther/M10', 'FV4202', 'Centurion Mk. 5/1 RAAC',
    'AMX Chasseur de chars', 'Panther mit 8,8 cm L/71', 'Strv 81',
    'Panzer 58', 'Lansen C', 'Obiekt 274a', 'Kampfpanzer 07 RH',
    '122 TM', 'Kpz. Pr.68 (P)', 'AltProto AMX 30',
    'M47 Patton Improved', 'Mars', 'GSOR 1010 FB', 'FV601 Saladin',
    'AMX 13 57', 'Panhard EBR 75 (FL 10)', 'HWK 30', 'M41D',
    'leKpz M 41 90 mm', 'ELC EVEN 90', 'M24E2 Super Chaffee', 'A46',
    'Staghound Mk. III', 'Aufklarungspanzer Panther',
    'VK 28.01 mit 10,5 cm L/28', 'SU-122-44', 'SU-100Y',
    'Dicker Max', 'ISU-122S', 'Rhm.-Borsig Waffentrager',
    'Rheinmetall Skorpion', 'Rheinmetall Skorpion G', 'GSOR 1008',
    'Kanonenjagdpanzer 105', 'E 25', 'Super Hellcat', 'M56 Scorpion',
    'Excalibur', 'Churchill Gun Carrier', "AMX Canon d'assaut 105",
    '105 leFH18B2', 'Bishop', 'SU-122A', 'KV-1 ekranirovanny',
    'IS-2 ekranirovanny', 'Matilda Black Prince', 'Valiant',
    'M4A3E2 Sherman Jumbo', 'Excelsior', 'Pz.Kpfw. B2 740 (f)',
    'Grosstraktor - Krupp', 'Pz.Kpfw. IV hydrostat.',
    'Type 3 Chi-Nu Kai', 'M4A2E4 Sherman', 'Ram II', 'Sherman III',
    'Renault G1', 'M4 Improved', 'DS PZInz', 'Cavalier',
    'AEC Armoured Car', 'VK 30.01 (H)', 'Pz.Kpfw. V/IV',
    'A-32', 'Mitsu 108', 'M24 No.594', 'M7',
    'A25 Harry Hopkins I', 'Pz.Kpfw. III/IV', 'Pz.Kpfw. III Ausf. K',
    'VK 30.01 (P)', 'Pz.Kpfw. KW I (r)', 'Bourrasque',
    'Progetto M35 mod. 46', 'CS-52 LIS'
}

def classify_tank(tag, name):
    """Определяет тип танка по тегу и названию"""
    # Проверяем коллекционные по названию
    if name in COLLECTOR_NAMES:
        return 'collector'
    
    # Проверяем премиумные по суффиксам в теге
    for suffix in PREMIUM_SUFFIXES:
        if suffix in tag:
            return 'premium'
    
    # По умолчанию - обычный прокачиваемый
    return 'regular'

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
    data = {'updated': datetime.now().strftime('%d.%m.%Y %H:%M'), 'periods': {}}
    for key, months in [('3m', 3), ('6m', 6), ('12m', 12), ('all', 999)]:
        print("Loading " + str(months) + " months...")
        tanks = fetch(months)
        for tank in tanks:
            tank['category'] = classify_tank(tank['tag'], tank['name'])
        data['periods'][key] = tanks
        print("Got " + str(len(tanks)) + " tanks")
    with open('data/tanks.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    total = sum(len(v) for v in data['periods'].values())
    print("Done! Saved " + str(total) + " records")

if __name__ == '__main__':
    main()
