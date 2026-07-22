import asyncio
import csv
import os
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.client.session.aiohttp import AiohttpSession
import aiohttp

BOT_TOKEN = "8772614838:AAFMOZLj2CLrdoiE0KVPS0Mff_S1u0mnxiM"
CSV_FILE = "schedule.csv"

# Возвращаем системный прокси PythonAnywhere
os.environ["HTTP_PROXY"] = "http://proxy.server:3128"
os.environ["HTTPS_PROXY"] = "http://proxy.server:3128"

# Сессия aiohttp с поддержкой прокси из переменных окружения
class PythonAnywhereSession(AiohttpSession):
    async def create_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                trust_env=True,
                json_serialize=self.json_dumps,
            )
        return self._session

session = PythonAnywhereSession()
bot = Bot(token=BOT_TOKEN, session=session)
dp = Dispatcher()

# Только вылеты ИЗ Москвы / СПб / Краснодара в страны назначения
SCHEDULE_TEMPLATE = [
    {"time_slot": "🌅 Утро", "passenger": "Сергей", "route": "Москва / СПб → Лондон", "airline": "British Airways", "flight": "BA-879", "dep": "08:30", "arr": "11:15"},
    {"time_slot": "🌅 Утро", "passenger": "Дарья", "route": "Москва / СПб → Корфу", "airline": "Aegean Airlines", "flight": "A3-402", "dep": "10:15", "arr": "14:40"},
    {"time_slot": "☀️ День", "passenger": "Валерия", "route": "Москва / СПб → Бангкок", "airline": "Qatar Airways", "flight": "QR-338", "dep": "14:20", "arr": "03:50 (+1)"},
    {"time_slot": "🌆 Вечер", "passenger": "Максим", "route": "Москва / Краснодар → Бангкок", "airline": "Aeroflot", "flight": "SU-270", "dep": "19:40", "arr": "08:30 (+1)"},
]

def init_monthly_csv():
    rows = [["Date", "TimeSlot", "Passenger", "Route", "Airline", "Flight", "Departure", "Arrival", "Status"]]
    today = datetime.now().date()
    
    for i in range(30):
        current_date = (today + timedelta(days=i)).strftime("%Y-%m-%d")
        for p in SCHEDULE_TEMPLATE:
            status = "Задерживается" if (i % 5 == 2 and p["passenger"] == "Максим") else "По расписанию"
            rows.append([current_date, p["time_slot"], p["passenger"], p["route"], p["airline"], p["flight"], p["dep"], p["arr"], status])

    with open(CSV_FILE, mode="w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerows(rows)

init_monthly_csv()

def get_person_schedule(person_name, date_str):
    if not os.path.exists(CSV_FILE): return "⚠️ Файл не найден."
    flights = []
    with open(CSV_FILE, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row.get("Date") == date_str and row.get("Passenger") == person_name:
                flights.append(row)
    if not flights: return f"✈️ Для **{person_name}** нет вылетов на этот день."
    
    formatted_date = datetime.strptime(date_str, "%Y-%m-%d").strftime("%d.%m.%Y")
    text = f"👤 **ВЫЛЕТЫ: {person_name.upper()}** ({formatted_date})\n"
    text += "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n\n"
    for f in flights:
        status_icon = "🟢" if f.get('Status') == "По расписанию" else "🟡"
        text += f"📍 **{f.get('Route', '')}**\n✈️ Рейс: {f.get('Airline', '')} ({f.get('Flight', '')})\n⏰ Вылет: **{f.get('Departure', '')}**\nСтатус: {status_icon} {f.get('Status', '')}\n\n"
    return text

def get_full_schedule(date_str):
    if not os.path.exists(CSV_FILE): return "⚠️ Файл не найден."
    flights = []
    with open(CSV_FILE, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row.get("Date") == date_str: flights.append(row)

    formatted_date = datetime.strptime(date_str, "%Y-%m-%d").strftime("%d.%m.%Y")
    text = f"📋 **ВСЕ ВЫЛЕТЫ** ({formatted_date})\n⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n\n"
    for f in flights:
        status_icon = "🟢" if f.get('Status') == "По расписанию" else "🟡"
        text += f"👤 **{f.get('Passenger', '')}**\n✈️ {f.get('Route', '')} | {f.get('Flight', '')} ({status_icon})\n"
    return text

def get_main_keyboard(date_str):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 Сергей", callback_data=f"user_Сергей_{date_str}"), InlineKeyboardButton(text="👤 Дарья", callback_data=f"user_Дарья_{date_str}")],
        [InlineKeyboardButton(text="👤 Валерия", callback_data=f"user_Валерия_{date_str}"), InlineKeyboardButton(text="👤 Максим", callback_data=f"user_Максим_{date_str}")],
        [InlineKeyboardButton(text="📋 Показать всё", callback_data=f"full_{date_str}")],
        [InlineKeyboardButton(text="📅 Сегодня", callback_data=f"date_{datetime.now().strftime('%Y-%m-%d')}"), InlineKeyboardButton(text="📅 Завтра", callback_data=f"date_{(datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')}")]
    ])
    return kb

@dp.message(Command("start"), Command("flights"))
async def start_handler(message: types.Message):
    today_str = datetime.now().strftime("%Y-%m-%d")
    await message.answer("👋 Выбери пассажира, чтобы узнать время вылета:", reply_markup=get_main_keyboard(today_str))

@dp.callback_query(F.data.startswith("user_"))
async def process_user_callback(callback: types.CallbackQuery):
    _, name, date = callback.data.split("_")
    await callback.message.edit_text(get_person_schedule(name, date), reply_markup=get_main_keyboard(date), parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data.startswith("full_"))
async def process_full_callback(callback: types.CallbackQuery):
    date = callback.data.split("full_")[1]
    await callback.message.edit_text(get_full_schedule(date), reply_markup=get_main_keyboard(date), parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data.startswith("date_"))
async def process_date_callback(callback: types.CallbackQuery):
    date = callback.data.split("date_")[1]
    await callback.message.edit_text("📅 Выбрана дата. Выбери пассажира:", reply_markup=get_main_keyboard(date), parse_mode="Markdown")
    await callback.answer()

async def main():
    print("Бот успешно запущен!")
    # Уменьшаем время ожидания long polling до 10 сек, чтобы прокси не разрывал соединение
    await dp.start_polling(bot, polling_timeout=10)

if __name__ == "__main__":
    asyncio.run(main())
