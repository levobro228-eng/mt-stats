import json
import os
import urllib.request
import urllib.parse

DB_URL = 'http://db.wotstat.info:80/?user=public'

def run_query(query, label):
    print("\n=== " + label + " ===")
    try:
        url = DB_URL + "&query=" + urllib.parse.quote(query)
        req = urllib.request.Request(url, method='GET', headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=30) as r:
            text = r.read().decode('utf-8')
        lines = text.strip().split('\n')
        print("Найдено строк: " + str(len(lines)))
        if len(lines) > 0:
            print("Первые 10 строк:")
            for line in lines[:10]:
                print("  " + line)
        return lines
    except Exception as e:
        print("Ошибка: " + str(e))
        return []

def main():
    print("Поиск танков 11 уровня по тегам")
    print("=" * 50)
    
    # Ищем конкретные теги танков 11 уровня
    tags = [
        'ussr:R124_Object_279',
        'germany:G182_Mausekonig',
        'germany:G184_EisBaer',
        'usa:A150_MBT_B',
        'china:Ch57_BZT_70',
        'france:F134_ARL_Projet_F',
        'uk:GB140_Champion'
    ]
    
    tag_list = "','".join(tags)
    q1 = "SELECT tankTag, tankLevel, count() as battles FROM Event_OnBattleResult WHERE region = 'RU' AND battleMode = 'REGULAR' AND dateTime >= now() - INTERVAL 6 MONTH AND tankTag IN ('" + tag_list + "') GROUP BY tankTag, tankLevel ORDER BY battles DESC"
    run_query(q1, "Танки 11 уровня по тегам (за 6 месяцев)")
    
    # Проверяем в TankList
    q2 = "SELECT tag, nameRU, level FROM TankList WHERE tag IN ('" + tag_list + "')"
    run_query(q2, "Эти же танки в TankList")
    
    # Ищем все танки с этими тегами за всё время
    q3 = "SELECT tankTag, tankLevel, count() as battles FROM Event_OnBattleResult WHERE region = 'RU' AND battleMode = 'REGULAR' AND tankTag IN ('" + tag_list + "') GROUP BY tankTag, tankLevel ORDER BY battles DESC"
    run_query(q3, "Танки 11 уровня по тегам (за всё время)")
    
    print("\n" + "=" * 50)
    print("Диагностика завершена")

if __name__ == '__main__':
    main()
