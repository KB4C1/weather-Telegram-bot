import logging
import json
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, BotCommand
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from datetime import datetime
from config import BOT_TOKEN
from weather import get_weather
from utils import load, save, regions, get_cities

def normalize_city_name(name: str) -> str:
    # Заміна всіх різновидів дефісів на звичайний дефіс
    return (
        name
        .replace('\u2011', '-')  # non-breaking hyphen
        .replace('\u2010', '-')  # hyphen
        .replace('\u2012', '-')  # figure dash
        .replace('\u2013', '-')  # en dash
        .replace('\u2014', '-')  # em dash
        .replace('\u2212', '-')  # minus sign
        .strip()
    )

main_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="👤Профіль", callback_data="profile")],
        [InlineKeyboardButton(text="🏙️Обрати місто", callback_data="show_letters")]
    ]
)

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

class Form(StatesGroup):
    waiting_for_name = State()

async def set_commands():
    commands = [
        BotCommand(command="profile", description="Переглянути профіль"),
    ]
    await bot.set_my_commands(commands)

def get_user_data(user_id):
    data = load()
    if user_id not in data:
        data[user_id] = {"name": "", "history": [], "city": ""}
    # Ensure all keys exist
    data[user_id].setdefault("name", "")
    data[user_id].setdefault("history", [])
    data[user_id].setdefault("city", "")
    return data

@dp.message(Command("start"))
async def start(msg: Message):
    user_id = str(msg.from_user.id)
    data = get_user_data(user_id)
    user_city = data[user_id].get("city", "")

    main_kb2 = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👤Профіль", callback_data="profile")],
            [InlineKeyboardButton(text="🏙️Обрати місто", callback_data="show_letters")],
            [InlineKeyboardButton(
                text="🔍Дізнатись погоду в моєму місті", callback_data=f"weather:{user_city}"
            )] if user_city else []
        ]
    )

    if not user_city:
        await msg.answer(
            "Привіт! Введи назву міста, щоб дізнатись погоду, або обери опцію нижче.",
            reply_markup=main_kb
        )
    else:
        await msg.answer(
            "Привіт знову! Обери опцію нижче або введи назву міста, щоб дізнатись погоду.",
            reply_markup=main_kb2
        )
    save(data)  # ensure new user saved

@dp.message(Command("profile"))
async def profile(msg: Message):
    user_id = str(msg.from_user.id)
    data = get_user_data(user_id)
    save(data)

    name = data[user_id]["name"] if data[user_id]["name"] else "Ім'я не задано"
    btn_text = "✏️Редагувати ім'я" if data[user_id]["name"] else "✏️Додати ім'я"
    user_city = data[user_id]["city"] if data[user_id]["city"] else "Місто не задано"

    profile_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=btn_text, callback_data="change_name")],
            [InlineKeyboardButton(text="🔍 Історія", callback_data="send_history")],
            [InlineKeyboardButton(text="🏙️Обрати місто", callback_data="show_letters")]
        ]
    )
    await msg.answer(f"👤Профіль👤\nІм'я: {name}\nМісто: {user_city}", reply_markup=profile_kb)

@dp.callback_query(F.data == "profile")
async def profile_callback(callback: CallbackQuery):
    await profile(callback.message)
    await callback.answer()

@dp.callback_query(F.data == "change_name")
async def change_name_handler(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введи своє ім'я:")
    await state.set_state(Form.waiting_for_name)
    await callback.answer()

@dp.message(Form.waiting_for_name)
async def process_name(msg: Message, state: FSMContext):
    user_id = str(msg.from_user.id)
    data = get_user_data(user_id)
    new_name = msg.text.strip()
    data[user_id]["name"] = new_name
    save(data[user_id]["name"])
    await msg.answer(f"Ім'я змінено на: {new_name}")
    await state.clear()

@dp.callback_query(F.data == "send_history")
async def send_history(callback: CallbackQuery):
    user_id = str(callback.from_user.id)
    data = get_user_data(user_id)
    history = data[user_id].get("history", [])
    if not history:
        await callback.message.answer("🕳️ Історія порожня.")
    else:
        text = "\n".join([f"🕒 {item['datetime']}: {item['query']}" for item in history])
        await callback.message.answer(f"📜 Твоя історія:\n{text}")
    await callback.answer()

def get_unique_letters():
    # regions має бути список міст
    return sorted(set(city[0].upper() for city in regions if city))

@dp.callback_query(F.data == "show_letters")
async def show_letters(callback: CallbackQuery):
    letters = get_unique_letters()
    buttons = [InlineKeyboardButton(text=letter, callback_data=f"letter:{letter}") for letter in letters]
    keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons[i:i + 4] for i in range(0, len(buttons), 4)])
    await callback.message.edit_text("Оберіть літеру міста:", reply_markup=keyboard)
    await callback.answer()

@dp.callback_query(F.data.startswith("letter:"))
async def show_cities(callback: CallbackQuery):
    letter = callback.data.split(":")[1]
    cities = get_cities(letter)
    buttons = [InlineKeyboardButton(text=c, callback_data=f"city:{c}") for c in cities]
    if not buttons:
        await callback.message.edit_text(f"Міст не знайдено на літеру '{letter}'.", reply_markup=None)
    else:
        buttons.append(InlineKeyboardButton(text="🔙 Назад", callback_data="show_letters"))
        keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons[i:i + 2] for i in range(0, len(buttons), 2)])
        await callback.message.edit_text(f"Міста на літеру '{letter}':", reply_markup=keyboard)
    await callback.answer()

@dp.callback_query(F.data.startswith("city:"))
async def select_city(callback: CallbackQuery):
    city = callback.data.split(":", 1)[1].strip()
    city = normalize_city_name(city)
    user_id = str(callback.from_user.id)
    data = get_user_data(user_id)
    data[user_id]["city"] = city
    save(data)
    await callback.message.answer(f"🏙️ {city} встановлено у профіль!")
    await callback.answer()

@dp.callback_query(F.data.startswith("add_city:"))
async def add_city_callback(callback: CallbackQuery):
    user_id = str(callback.from_user.id)
    city = callback.data.split(":", 1)[1].strip()
    city = normalize_city_name(city)
    data = get_user_data(user_id)
    data[user_id]["city"] = city
    save(data)
    await callback.message.answer(f"🏙️ {city} встановлено у профіль!")
    await callback.answer()

@dp.callback_query(F.data.startswith("weather:"))
async def weather_in_city(callback: CallbackQuery):
    city = callback.data.split(":", 1)[1].strip()
    city = normalize_city_name(city)
    weather_info = get_weather(city)
    if weather_info:
        await callback.message.answer(weather_info)
    else:
        await callback.message.answer("Місто не знайдено. Перевірь назву.")
    await callback.answer()

@dp.message()
async def get_weather_handler(msg: Message):
    user_id = str(msg.from_user.id)
    data = get_user_data(user_id)
    city = normalize_city_name(msg.text)
    weather_info = get_weather(city)

    if weather_info:
        data[user_id]["history"].append({
            "query": city,
            "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        save(data)

        city_kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🏙️ Додати місто як своє", callback_data=f"add_city:{city}")]
            ]
        )

        if data[user_id].get("city") == city:
            await msg.answer(weather_info)
        elif data[user_id].get("city") == "":
            await msg.answer(weather_info, reply_markup=city_kb)
        else:
            await msg.answer(weather_info)
    else:
        await msg.answer("Місто не знайдено. Перевірь назву.")

async def main():
    print("✅ Бот працює")
    await set_commands()
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())