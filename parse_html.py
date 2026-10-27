import json
import os
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def parse_html_file(filepath, category):
    if not os.path.exists(filepath):
        print(f"Файл не найден: {filepath}")
        return []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    tanks = []
    
    # Ищем паттерны с данными танков
    # Формат: ./файл_иконки.svg\nНазвание танка
    pattern = r'\./[^/]+/(ussr|germany|usa|china|france|uk|japan|czech|sweden|poland|italy|intunion)-[^"]+\.svg\n(БазоваяУлучшенная\n)?([^\n]+)\n'
    
    matches = re.findall(pattern, content)
    
    for match in matches:
        nation_code = match[0]
        name = match[2].strip()
        
        if not name or len(name) < 2:
            continue
        
        tanks.append({
            'name': name,
            'nation': nation_code,
            'category': category
        })
    
    return tanks

def main():
    print("Парсинг HTML-файлов...")
    
    collectors_file = os.path.join(BASE_DIR, 'колекционные.html')
    collectors = parse_html_file(collectors_file, 'collector')
    print(f"Найдено {len(collectors)} коллекционных танков")
    
    premiums_file = os.path.join(BASE_DIR, 'премиум_наградная.html')
    premiums = parse_html_file(premiums_file, 'premium')
    print(f"Найдено {len(premiums)} премиум танков")
    
    all_tanks = collectors + premiums
    
    output_file = os.path.join(BASE_DIR, 'tankopedia_data.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_tanks, f, ensure_ascii=False, indent=2)
    
    print(f"Всего сохранено {len(all_tanks)} танков в {output_file}")

if __name__ == '__main__':
    main()
