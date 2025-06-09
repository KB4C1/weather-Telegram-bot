#                     Weather Telegram Bot 🌤

Simple Telegram bot to get weather updates for any city using a weather API.

---

## Features

- Get current weather by city name
- Save user preferences locally
- Simple commands for easy use

---

## Setup

1. Clone this repo:
   ```bash
   git clone https://github.com/KB4C1/weather-Telegram-bot.git
   cd weather-Telegram-bot
**2.Create a config.py file in the project root with the following content:**

wAPI = "OpenWeatherMap_API_TOKEN"
BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
Replace "YOUR_WEATHER_API_TOKEN" and "YOUR_TELEGRAM_BOT_TOKEN" with your actual tokens.

3. Install required packages:
   
pip install -r requirements.txt
5. Run the bot:

python bot.py
## Usage
Start the bot on Telegram with /start

To get Weather enter city name

Make sure to have a stable internet connection for API calls

Bot saves user data locally in users.json

Troubleshooting
If you get errors related to missing modules, make sure to install all dependencies via pip install -r requirements.txt

API errors usually mean your API token is invalid or rate-limited

If bot doesn’t respond, check your internet connection and Telegram token
