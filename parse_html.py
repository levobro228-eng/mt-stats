import json
import os
from bs4 import BeautifulSoup

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def parse_html_file(filepath, category):
    """Парсит HTML-файл и извлекает данные о танках"""
    if not os.path.exists(filepath):
        print(f"Файл не найден: {filepath}")
        return []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    soup = BeautifulSoup(content, 'html.parser')
    tanks = []
    
    # Ищем все строки таблицы с танками
    rows = soup.find_all('tr', class_='tankopedia-row')
    
    for row in rows:
        cells = row.find_all('td')
        if len(cells) < 5:
            continue
        
        # Извлекаем данные из ячеек
        level_text = cells[2].get_text(strip=True) if len(cells) > 2 else ''
        name_cell = cells[3] if len(cells) > 3 else None
        type_cell = cells[4] if len(cells) > 4 else None
        
        if not name_cell:
            continue
        
        # Название танка
        name = name_cell.get_text(strip=True)
        if not name:
            continue
        
        # Уровень (римские цифры)
        level_map = {'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5, 'VI': 6, 'VII': 7, 'VIII': 8, 'IX': 9, 'X': 10, 'XI': 11}
        level = level_map.get(level_text, 0)
        
        # Тип танка (извлекаем из ссылки на иконку)
        tank_type = 'unknown'
        icon_img = cells[1].find('img') if len(cells) > 1 else None
        if icon_img and icon_img.get('src'):
            src = icon_img['src']
            if 'lighttank' in src:
                tank_type = 'ЛТ'
            elif 'mediumtank' in src:
                tank_type = 'СТ'
            elif 'heavytank' in src:
                tank_type = 'ТТ'
            elif 'at-spg' in src:
                tank_type = 'ПТ-САУ'
            elif 'spg' in src:
                tank_type = 'САУ'
        
        # Нация (извлекаем из пути к иконке танка)
        nation = 'unknown'
        name_link = name_cell.find('a')
        if name_link and name_link.get('href'):
            href = name_link['href']
            # Пример: ./коллекционные_files/ussr-R09_T-26.svg
            if 'ussr' in href:
                nation = 'ussr'
            elif 'germany' in href:
                nation = 'germany'
            elif 'usa' in href:
                nation = 'usa'
            elif 'china' in href:
                nation = 'china'
            elif 'france' in href:
                nation = 'france'
            elif 'uk' in href or 'gb' in href:
                nation = 'uk'
            elif 'japan' in href:
                nation = 'japan'
            elif 'czech' in href:
                nation = 'czech'
            elif 'sweden' in href:
                nation = 'sweden'
            elif 'poland' in href:
                nation = 'poland'
            elif 'italy' in href:
                nation = 'italy'
            elif 'intunion' in href:
                nation = 'intunion'
        
        tanks.append({
            'name': name,
            'level': level,
            'type': tank_type,
            'nation': nation,
            'category': category
        })
    
    return tanks

def main():
    print("Парсинг HTML-файлов...")
    
    # Парсим файл с коллекционными танками
    collectors_file = os.path.join(BASE_DIR, 'колекционные.html')
    collectors = parse_html_file(collectors_file, 'collector')
    print(f"Найдено {len(collectors)} коллекционных танков")
    
    # Парсим файл с премиум танками
    premiums_file = os.path.join(BASE_DIR, 'премиум_наградная.html')
    premiums = parse_html_file(premiums_file, 'premium')
    print(f"Найдено {len(premiums)} премиум танков")
    
    # Объединяем все танки
    all_tanks = collectors + premiums
    
    # Сохраняем в JSON
    output_file = os.path.join(BASE_DIR, 'tankopedia_data.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_tanks, f, ensure_ascii=False, indent=2)
    
    print(f"Всего сохранено {len(all_tanks)} танков в {output_file}")
    
    # Статистика
    levels = {}
    nations = {}
    types = {}
    for t in all_tanks:
        levels[t['level']] = levels.get(t['level'], 0) + 1
        nations[t['nation']] = nations.get(t['nation'], 0) + 1
        types[t['type']] = types.get(t['type'], 0) + 1
    
    print("\nРаспределение по уровням:")
    for lvl in sorted(levels.keys()):
        print(f"  Уровень {lvl}: {levels[lvl]} танков")
    
    print("\nРаспределение по нациям:")
    for nat in sorted(nations.keys()):
        print(f"  {nat}: {nations[nat]} танков")
    
    print("\nРаспределение по типам:")
    for typ in sorted(types.keys()):
        print(f"  {typ}: {types[typ]} танков")

if __name__ == '__main__':
    main()
