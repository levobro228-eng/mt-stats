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
            print("Первые 5 строк:")
            for line in lines[:5]:
                print("  " + line)
        return lines
    except Exception as e:
        print("Ошибка: " + str(e))
        return []

def main():
    print("Диагностика базы wotstat.info")
    print("=" * 50)
    
    # Запрос 1: Сколько всего танков в TankList с уровнем 11?
    q1 = "SELECT tag, nameRU, level FROM TankList WHERE level = 11 AND nameRU != '' LIMIT 20"
    run_query(q1, "Танки 11 уровня в TankList")
    
    # Запрос 2: Какие вообще уровни есть в TankList?
    q2 = "SELECT level, count() as cnt FROM TankList WHERE nameRU != '' GROUP BY level ORDER BY level"
    run_query(q2, "Распределение танков по уровням в TankList")
    
    # Запрос 3: Есть ли бои на танках 11 уровня?
    q3 = "SELECT tankTag, count() as battles FROM Event_OnBattleResult WHERE region = 'RU' AND battleMode = 'REGULAR' AND dateTime >= now() - INTERVAL 6 MONTH GROUP BY tankTag HAVING battles > 10 ORDER BY battles DESC LIMIT 20"
    run_query(q3, "Топ-20 танков по боям за 6 месяцев")
    
    # Запрос 4: Попробуем найти танки 11 уровня через JOIN
    q4 = "SELECT e.tankTag, t.nameRU, e.level, count() as battles FROM Event_OnBattleResult e LEFT JOIN TankList t ON e.tankTag = t.tag WHERE e.region = 'RU' AND e.battleMode = 'REGULAR' AND e.dateTime >= now() - INTERVAL 6 MONTH AND t.level = 11 GROUP BY e.tankTag, t.nameRU, e.level ORDER BY battles DESC LIMIT 20"
    run_query(q4, "Танки 11 уровня с боями (JOIN)")
    
    # Запрос 5: Проверим теги танков 11 уровня из TankList
    q5 = "SELECT tag, nameRU, level FROM TankList WHERE nameRU LIKE '%279%' OR nameRU LIKE '%Mause%' OR nameRU LIKE '%Eis%' OR nameRU LIKE '%MBT-B%' OR nameRU LIKE '%Champion%' OR nameRU LIKE '%BZT%' OR nameRU LIKE '%ARL Projet%'"
    run_query(q5, "Поиск известных танков 11 уровня по имени")
    
    print("\n" + "=" * 50)
    print("Диагностика завершена")

if __name__ == '__main__':
    main()
