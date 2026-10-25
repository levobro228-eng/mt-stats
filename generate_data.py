import json
import os
import time
import urllib.request
import urllib.parse
from datetime import datetime

PREMIUM_TANKS = {
    'КВ-220-2', 'КВ-220-2 Бета-Тест', 'Черчилль III', 'ИС-6', 'КВ-5',
    'Somua SM', 'Caernarvon Action X', 'Chrysler K', 'Chrysler K GF',
    'AMX M4 mle. 49', 'AMX M4 mle. 49 Liberté', 'WZ-111 Alpine Tiger',
    'VK 168.01 (P)', 'VK 168.01 Mauerbrecher', '112', 'FCM 50 t',
    'M6A2E1', 'Charlemagne', 'WZ-111 model 6', 'BZ-176', 'Bisonte C45',
    'Caliban', 'Gonsalo', 'Löwe', 'Кировец-1', 'EMIL 1951',
    'Bourrasque', 'Progetto M35 mod. 46', 'CS-52 LIS', 'Cromwell B',
    'Pudel', 'M4A1 Revalorisé', 'Bretagne Panther', 'Sherman VC Firefly',
    'Pz.Kpfw. IV Schmalturm', 'AC 4 Experimental', 'M4A3E8 Fury',
    'Chimera', 'Panzer 58 Mutz', 'Primo Victoria', 'M48A2 Räumpanzer',
    'CS-52 C', 'T26E3 Eagle 7', 'Panther/M10', 'FV4202',
    'Centurion Mk. 5/1 RAAC', 'AMX Chasseur de chars', 'Panther mit 8,8 cm L/71',
    'Strv 81', 'Panzer 58', 'Lansen C', 'Объект 274а',
    'Kampfpanzer 07 RH', '122 TM', 'Kpz. Pr.68 (P)', 'AltProto AMX 30',
    'M47 Patton Improved', 'Марс', 'GSOR 1010 FB', 'FV601 Saladin',
    'AMX 13 57', 'Panhard EBR 75 (FL 10)', 'HWK 30', 'M41D',
    'leKpz M 41 90 mm', 'ELC EVEN 90', 'M24E2 Super Chaffee', 'A46',
    'Staghound Mk. III', 'Aufklärungspanzer Panther', 'VK 28.01 mit 10,5 cm L/28',
    'СУ-122-44', 'СУ-100Y', 'Dicker Max', 'ИСУ-122С', 'Rhm.-Borsig Waffenträger',
    'Rheinmetall Skorpion', 'Rheinmetall Skorpion G', 'GSOR 1008',
    'Kanonenjagdpanzer 105', 'E 25', 'Super Hellcat', 'M56 Scorpion',
    'Excalibur', 'Churchill Gun Carrier', "AMX Canon d'assaut 105",
    '105 leFH18B2', 'Bishop', 'СУ-122А', 'КВ-1 экранированный',
    'ИС-2 экранированный', 'Матильда IV', 'К-2', 'ИС-2М',
    'КВ-4 Креславского', 'Объект 252У', 'Объект 252У Защитник',
    'Сапсан', 'Защитник', 'Бисонте', 'Matilda Black Prince',
    'Valiant', 'M4A3E2 Sherman Jumbo', 'Excelsior', 'Pz.Kpfw. B2 740 (f)',
    'Großtraktor - Krupp', 'Pz.Kpfw. IV hydrostat.', 'Type 3 Chi-Nu Kai',
    'M4A2E4 Sherman', 'Ram II', 'Sherman III', 'Renault G1', 'M4 Improved',
    'DS PZInż', 'Cavalier', 'AEC Armoured Car', 'VK 30.01 (H)',
    'Pz.Kpfw. V/IV', 'А-32', 'Mitsu 108', 'M24 No.594', 'M7',
    'A25 Harry Hopkins I', 'Pz.Kpfw. III/IV', 'Pz.Kpfw. III Ausf. K',
    'VK 30.01 (P)', 'Pz.Kpfw. KW I (r)'
}

COLLECTOR_TANKS = {
    'КВ-1С с МЗ', 'Объект 244', 'КВ-2 (Р)', 'Матильда IV',
    'К-2', 'ИС-2М', 'КВ-4 Креславского', 'Объект 252У',
    'КВ-220-2', 'Черчилль III', 'ИС-6', 'КВ-5',
    'Объект 252У Защитник', 'Сапсан', 'Защитник', 'Бисонте',
    'EMIL 1951', 'Löwe', 'Кировец-1', 'Gonsalo', 'M6A2E1',
    'Charlemagne', 'WZ-111 model 6', 'BZ-176', 'Bisonte C45',
    'Caliban', 'Somua SM', 'Caernarvon Action X', 'Chrysler K',
    'Chrysler K GF', 'AMX M4 mle. 49', 'AMX M4 mle. 49 Liberté',
    'WZ-111 Alpine Tiger', 'VK 168.01 (P)', 'VK 168.01 Mauerbrecher',
    '112', 'FCM 50 t'
}

def classify_tank(name):
    if name in COLLECTOR_TANKS:
        return 'collector'
    elif name in PREMIUM_TANKS:
        return 'premium'
    return 'regular'

TYPE_MAP = {
    'LT': 'ЛТ', 'MT': 'СТ', 'HT': 'ТТ', 'AT': 'ПТ-САУ', 'SPG': 'САУ'
}

CLICKHOUSE_URL = 'http://db.wotstat.info:80/?user=public'

def fetch_data(months, max_retries=3):
    min_battles = 300 if months <= 6 else 1000
    
    query = f"""
    SELECT 
        t.nameRU AS tank_name,
        t.shortNameRU AS short_name,
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
          AND dateTime >= now() - INTERVAL {months} MONTH
          AND tankTag NOT LIKE '%_Gold%'
          AND tankTag NOT LIKE '%_Prem%'
          AND tankTag NOT LIKE '%_MK%'
          AND tankTag NOT LIKE '%_Patton%'
          AND tankTag NOT LIKE '%_prot%'
          AND tankTag NOT LIKE '%_CFE_%'
          AND tankTag NOT LIKE '%_3D%'
          AND tankTag NOT LIKE '%_Beijing_Opera%'
          AND tankTag NOT LIKE '%_QL%'
          AND tankTag NOT LIKE '%_CN%'
          AND tankTag NOT LIKE '%_CO%'
          AND tankTag NOT LIKE '%_DV%'
          AND tankTag NOT LIKE '%_BF%'
          AND tankTag NOT LIKE '%_GrandFinal%'
          AND tankTag NOT LIKE '%_FL%'
          AND tankTag NOT LIKE '%_SH%'
          AND tankTag NOT LIKE '%_WT24_%'
          AND tankTag NOT LIKE '%_IC4_%'
          AND tankTag NOT LIKE '%_Ziqiang%'
          AND tankTag NOT LIKE '%_Yong_Bing%'
          AND tankTag NOT LIKE '%_Yongshi%'
          AND tankTag NOT LIKE '%_T'
        GROUP BY tankTag, tankLevel, tankType
        HAVING total_battles > {min_battles}
    ) e
    LEFT JOIN TankList t ON e.tankTag = t.tag
    WHERE t.nameRU IS NOT NULL
    ORDER BY e.level ASC, e.type ASC, e.win_rate DESC
    """
    
    for attempt in range(max_retries):
        try:
            print(f"  Попытка {attempt + 1}/{max_retries}...")
            
            url = f"{CLICKHOUSE_URL}&query={urllib.parse.quote(query)}"
            
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
                if len(parts) >= 7:
                    name, short_name, level, tank_type, battles, wins, win_rate = parts[:7]
                    tanks.append({
                        'name': name,
                        'short_name': short_name,
                        'level': int(level),
                        'type': TYPE_MAP.get(tank_type, tank_type),
                        'type_code': tank_type,
                        'battles': int(battles),
                        'wins': int(wins),
                        'win_rate': float(win_rate),
                        'category': classify_tank(name)
                    })
            return tanks
        except Exception as e:
            print(f"  Ошибка: {e}")
            if attempt < max_retries - 1:
                print("  Ждём 5 секунд...")
                time.sleep(5)
    
    raise Exception(f"Не удалось получить данные после {max_retries} попыток")

def main():
    print("Генерация данных...")
    os.makedirs('data', exist_ok=True)
    
    data = {
        'updated': datetime.now().strftime('%d.%m.%Y %H:%M'),
        'periods': {}
    }
    
    periods = {
        '3m': 3,
        '6m': 6,
        '12m': 12,
        'all': 999
    }
    
    for key, months in periods.items():
        print(f"Загрузка данных за {months} мес...")
        data['periods'][key] = fetch_data(months)
        print(f"  Получено {len(data['periods'][key])} танков")
    
    with open('data/tanks.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    total = sum(len(v) for v in data['periods'].values())
    print(f"\nГотово! Сохранено {total} записей в data/tanks.json")

if __name__ == '__main__':
    main()
