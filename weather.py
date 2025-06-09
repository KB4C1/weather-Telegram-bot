import requests
from config import wAPI

BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

def get_weather(city):
    params = {
        "q": city,
        "appid": wAPI,
        "units": "metric",
        "lang": "ua"
    }

    r = requests.get(BASE_URL, params=params)

    if r.status_code == 200:
        data = r.json()
        name = data["name"]
        temp = data["main"]["temp"]
        feels_like = data["main"]["feels_like"]
        description = data["weather"][0]["description"].capitalize()
        wind = data["wind"]["speed"]

        return (
            f"Місто: {name}\n"
            f"Температура: {temp}°C\n"
            f"Відчувається як: {feels_like}°C\n"
            f"Погода: {description}\n"
            f"Вітер: {wind} м/с"
        )
    elif r.status_code == 404:
        return "Місто не знайдено. Перевірь назву"
    else:
        return "Щось пішло не так з погодою..."
