import json

def load():
    try:
        with open("users.json", "r", encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError:
        data = {}
    return data

def save(data):
    with open("users.json", "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

regions = [
    "Вінниця",
    "Волинь",
    "Дніпро",
    "Донецьк",
    "Житомир",
    "Закарпаття",
    "Запоріжжя",
    "Івано‑Франківськ",
    "Київ",
    "Кіровоград",
    "Луганськ",
    "Львів",
    "Миколаїв",
    "Одесса",
    "Полтава",
    "Рівне",
    "Сумська область",
    "Тернопіль",
    "Харків",
    "Херсон",
    "Хмельниччина",
    "Черкаси",
    "Чернівці",
    "Чернігів",
    "Севастополь"
]

def __init__():
    pass

def get_cities(letter):
    cities = []
    for city in regions:
        if city.startswith(letter.upper()):
            cities.append(city)
    
    return cities
