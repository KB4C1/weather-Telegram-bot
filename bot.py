import re
from datetime import datetime

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    Message, InlineKeyboardMarkup, InlineKeyboardButton,
    CallbackQuery, BotCommand,
)

from config import BOT_TOKEN
from weather import get_weather
from utils import load, save, regions, get_cities

CITY_NAME_PATTERN = re.compile(r"^[\wа-яА-ЯіїєґІЇЄҐ' -]{1,32}$", re.UNICODE)

def normalize_city_name(name: str) -> str:
    return (
        name
        .replace('\u2011', '-')
        .replace('\u2010', '-')
        .replace('\u2012', '-')
        .replace('\u2013', '-')
        .replace('\u2014', '-')
        .replace('\u2212', '-')
        .strip()
    )
    
def is_valid_name(name: str) -> bool:
    name = name.strip()
    return 1 <= len(name) <= 32 and CITY_NAME_PATTERN.fullmatch(name) is not None


def ensure_user(users_data: dict, user_id: str) -> None:
    if user_id not in users_data:
        users_data[user_id] = {"name": "", "history": [], "city": ""}


def profile_keyboard(user_data: dict) -> InlineKeyboardMarkup:
    btn_text = "✏️Редагувати ім'я" if user_data["name"] else "✏️Додати ім'я"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=btn_text, callback_data="change_name")],
            [InlineKeyboardButton(text="🔍 Історія", callback_data="send_history")],
            [InlineKeyboardButton(text="🏙️Обрати місто", callback_data="show_letters")],
            [InlineKeyboardButton(text="↩️Назад", callback_data="back")],
        ]
    )


def main_keyboard_with_weather(user_city: str) -> InlineKeyboardMarkup:
    kb = [
        [InlineKeyboardButton(text="👤Профіль", callback_data="profile")],
        [InlineKeyboardButton(text="🏙️Обрати місто", callback_data="show_letters")],
    ]
    if user_city:
        kb.append([
            InlineKeyboardButton(
                text="🔍Дізнатись погоду в моєму місті",
                callback_data=f"weather:{user_city}",
            )
        ])
    return InlineKeyboardMarkup(inline_keyboard=kb)


def get_unique_letters() -> list[str]:
    return sorted(set(city[0].upper() for city in regions if city))


def choose_letter_keyboard(letters: list[str]) -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton(text=letter, callback_data=f"letter:{letter}")
        for letter in letters
    ]
    keyboard = [buttons[i:i + 4] for i in range(0, len(buttons), 4)]
    keyboard.append([InlineKeyboardButton(text="↩️Назад", callback_data="back")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def choose_city_keyboard(cities: list[str]) -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton(text=c, callback_data=f"city:{c}") for c in cities
    ]
    if buttons:
        buttons.append(InlineKeyboardButton(text="🔙 Назад", callback_data="show_letters"))
    return InlineKeyboardMarkup(
        inline_keyboard=[buttons[i:i + 2] for i in range(0, len(buttons), 2)]
    )


def city_add_keyboard(city: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🏙️ Додати місто як своє",
                    callback_data=f"add_city:{city}",
                )
            ]
        ]
    )

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)


class Form(StatesGroup):

    waiting_for_name = State()


async def set_commands() -> None:

    commands = [
        BotCommand(command="profile", description="Переглянути профіль"),
    ]
    await bot.set_my_commands(commands)


async def show_profile(msg_or_callback, users_data: dict, user_id: str) -> None:

    user_data = users_data[user_id]
    name = user_data["name"] or "Ім'я не задано"
    city = user_data["city"] or "Місто не задано"
    kb = profile_keyboard(user_data)
    await msg_or_callback.answer(
        f"👤Профіль👤\nІм'я: {name}\nМісто: {city}", reply_markup=kb
    )

@dp.message(Command("start"))
async def start(msg: Message, state: FSMContext) -> None:
    await state.clear()
    user_id = str(msg.from_user.id)
    users_data = load()
    ensure_user(users_data, user_id)
    user_city = users_data[user_id].get("city", "")
    kb = main_keyboard_with_weather(user_city)
    text = (
        "Привіт! Введи назву міста, щоб дізнатись погоду, або обери опцію нижче."
        if not user_city else
        "Привіт знову! Обери опцію нижче або введи назву міста, щоб дізнатись погоду."
    )
    await msg.answer(text, reply_markup=kb)
    save(users_data)


@dp.message(Command("profile"))
async def profile(msg: Message, state: FSMContext) -> None:

    await state.clear()
    user_id = str(msg.from_user.id)
    users_data = load()
    ensure_user(users_data, user_id)
    await show_profile(msg, users_data, user_id)
    save(users_data)


@dp.callback_query(F.data == "profile")
async def profile_callback(callback: CallbackQuery, state: FSMContext) -> None:

    await state.clear()
    user_id = str(callback.from_user.id)
    users_data = load()
    ensure_user(users_data, user_id)
    await show_profile(callback.message, users_data, user_id)
    await callback.answer()


@dp.callback_query(F.data == "back")
async def back(callback: CallbackQuery, state: FSMContext) -> None:

    await state.clear()
    user_id = str(callback.from_user.id)
    users_data = load()
    ensure_user(users_data, user_id)
    user_city = users_data[user_id].get("city", "")
    kb = main_keyboard_with_weather(user_city)
    text = (
        "Привіт! Введи назву міста, щоб дізнатись погоду, або обери опцію нижче."
        if not user_city else
        "Привіт знову! Обери опцію нижче або введи назву міста, щоб дізнатись погоду."
    )
    await callback.message.answer(text, reply_markup=kb)
    await callback.answer()


@dp.callback_query(F.data == "change_name")
async def change_name_handler(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.answer("Введи своє ім'я (до 32 символів, лише букви, пробіли, дефіси):")
    await state.set_state(Form.waiting_for_name)
    await callback.answer()


@dp.message(Form.waiting_for_name)
async def process_name(msg: Message, state: FSMContext) -> None:
    user_id = str(msg.from_user.id)
    users_data = load()
    ensure_user(users_data, user_id)
    new_name = msg.text.strip()
    if not is_valid_name(new_name):
        await msg.answer("❌ Некоректне ім'я! Дозволено тільки букви, пробіли, дефіси, до 32 символів.")
        return
    users_data[user_id]["name"] = new_name
    save(users_data)
    await msg.answer(f"Ім'я змінено на: {new_name}")
    await show_profile(msg, users_data, user_id)
    await state.clear()


@dp.callback_query(F.data == "send_history")
async def send_history(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    user_id = str(callback.from_user.id)
    users_data = load()
    ensure_user(users_data, user_id)
    history = users_data[user_id].get("history", [])
    if not history:
        await callback.message.answer("🕳️ Історія порожня.")
    else:
        text = "\n".join(
            [f"🕒 {item['datetime']}: {item['query']}" for item in history]
        )
        await callback.message.answer(f"📜 Твоя історія:\n{text}")
    await callback.answer()


@dp.callback_query(F.data == "show_letters")
async def show_letters(callback: CallbackQuery, state: FSMContext) -> None:

    await state.clear()
    letters = get_unique_letters()
    keyboard = choose_letter_keyboard(letters)
    await callback.message.edit_text("Оберіть літеру міста:", reply_markup=keyboard)
    await callback.answer()


@dp.callback_query(F.data.startswith("letter:"))
async def show_cities(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    letter = callback.data.split(":")[1]
    cities = get_cities(letter)
    keyboard = choose_city_keyboard(cities)
    if not cities:
        await callback.message.edit_text(f"Міст не знайдено на літеру '{letter}'.", reply_markup=None)
    else:
        await callback.message.edit_text(f"Міста на літеру '{letter}':", reply_markup=keyboard)
    await callback.answer()


@dp.callback_query(F.data.startswith("city:"))
async def select_city(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    city = normalize_city_name(callback.data.split(":", 1)[1].strip())
    if not is_valid_name(city):
        await callback.message.answer("❌ Некоректна назва міста!")
        await callback.answer()
        return
    user_id = str(callback.from_user.id)
    users_data = load()
    ensure_user(users_data, user_id)
    users_data[user_id]["city"] = city
    save(users_data)
    await callback.message.answer(f"🏙️ {city} встановлено у профіль!")
    await show_profile(callback.message, users_data, user_id)
    await callback.answer()


@dp.callback_query(F.data.startswith("add_city:"))
async def add_city_callback(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    user_id = str(callback.from_user.id)
    city = normalize_city_name(callback.data.split(":", 1)[1].strip())
    if not is_valid_name(city):
        await callback.message.answer("❌ Некоректна назва міста!")
        await callback.answer()
        return
    users_data = load()
    ensure_user(users_data, user_id)
    users_data[user_id]["city"] = city
    save(users_data)
    await callback.message.answer(f"🏙️ {city} встановлено у профіль!")
    await show_profile(callback.message, users_data, user_id)
    await callback.answer()


@dp.callback_query(F.data.startswith("weather:"))
async def weather_in_city(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    city = normalize_city_name(callback.data.split(":", 1)[1].strip())
    if not is_valid_name(city):
        await callback.message.answer("❌ Некоректна назва міста!")
        await callback.answer()
        return
    weather_info = get_weather(city)
    if weather_info:
        await callback.message.answer(weather_info)
    else:
        await callback.message.answer("Місто не знайдено. Перевірь назву.")
    await callback.answer()


@dp.message()
async def get_weather_handler(msg: Message, state: FSMContext) -> None:
    await state.clear()
    user_id = str(msg.from_user.id)
    users_data = load()
    ensure_user(users_data, user_id)
    city = normalize_city_name(msg.text)
    if not is_valid_name(city):
        await msg.answer("❌ Некоректна назва міста! Введіть коректну назву.")
        return

    weather_info = get_weather(city)
    add_city_kb = city_add_keyboard(city)

    if weather_info and "Місто не знайдено" not in weather_info:
        users_data[user_id]["history"].append({
            "query": city,
            "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "details": "success",
        })
        save(users_data)
        if users_data[user_id].get("city") != city:
            await msg.answer(weather_info, reply_markup=add_city_kb)
        else:
            await msg.answer(weather_info)
    else:
        users_data[user_id]["history"].append({
            "query": city,
            "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "details": "failed",
        })
        save(users_data)
        await msg.answer("Місто не знайдено. Перевірь назву.")


async def main() -> None:
    print("✅ Бот працює")
    await set_commands()
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
