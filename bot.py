import asyncio
import csv
import os
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.client.session.aiohttp import AiohttpSession

BOT_TOKEN = "8772614838:AAFMOZLj2CLrdoiE0KVPS0Mff_S1u0mnxiM"
CSV_FILE = "schedule.csv"

session = AiohttpSession(proxy="http://proxy.server:3128")
bot = Bot(token=BOT_TOKEN, session=session)
dp = Dispatcher()

# Шаблоны рейсов с утра до ночи для каждого человека
SCHEDULE_TEMPLATE = [
    # Утро (06:00 - 12:00)
    {"time_slot": "🌅 Утро", "passenger": "Сергей", "route": "Москва / СПб → Лондон", "airline": "British Airways", "flight": "BA-879", "dep": "08:30", "arr": "11:15"},
    {"time_slot": "🌅 Утро", "passenger": "Дарья", "route": "Москва / СПб → Корфу", "airline": "Aegean Airlines", "flight": "A3-402", "dep": "10:15", "arr": "14:40"},
    
    # День (12:00 - 18:00)
    {"time_slot": "☀️ День", "passenger": "Валерия", "route": "Москва / СПб → Бангкок", "airline": "Qatar Airways", "flight": "QR-338", "dep": "14:20", "arr": "03:50 (+1)"},
    {"time_slot": "☀️ День", "passenger": "Сергей", "route": "Лондон → Москва / СПб", "airline": "British Airways", "flight": "BA-880", "dep": "16:00", "arr": "22:30"},

    # Вечер (18:00 - 00:00)
    {"time_slot": "🌆 Вечер", "passenger": "Максим", "route": "Москва / Краснодар → Бангкок", "airline": "Aeroflot", "flight": "SU-270", "dep": "19:40", "arr": "08:30 (+1)"},
    {"time_slot": "🌆 Вечер", "passenger": "Дарья", "route": "Корфу → Москва / СПб", "airline": "Aegean Airlines", "flight": "A3-403", "dep": "21:10", "arr": "01:35 (+1)"},

    # Ночь (00:00 - 06:00)
    {"time_slot": "🌙 Ночь", "passenger": "Валерия", "route": "Бангкок → Москва / СПб", "airline": "Qatar Airways", "flight": "QR-339", "dep": "01:15", "arr": "07:45"},
    {"time_slot": "🌙 Ночь", "passenger": "Максим", "route": "Бангкок → Москва / Краснодар", "airline": "Aeroflot", "flight": "SU-271", "dep": "03:50", "arr": "10:20"},
]

def init_monthly_csv():
    """Генерирует подробное расписание с утра до ночи на 30 дней вперед"""
    rows = [["Date", "TimeSlot", "Passenger", "Route", "Airline", "Flight", "Departure", "Arrival", "Status"]]
    
    today = datetime.now().date()
    
    for i in range(30):
        current_date = (today + timedelta(days=i)).strftime("%Y-%m-%d")
        
        for p in SCHEDULE_TEMPLATE:
            # Небольшая задержка для реалистичности
            status = "Задерживается" if (i % 5 == 2 and p["passenger"] == "Максим") else "По расписанию"
            
            rows.append([
                current_date,
                p["time_slot"],
                p["passenger"],
                p["route"],
                p["airline"],
                p["flight"],
                p["dep"],
                p["arr"],
                status
            ])

    with open(CSV_FILE, mode="w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerows(rows)

init_monthly_csv()

def get_person_schedule(person_name, date_str):
    """Возвращает рейсы только конкретного человека"""
    if not os.path.exists(CSV_FILE):
        return "⚠️ Файл с расписанием не найден."

    flights = []
    with open(CSV_FILE, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row.get("Date") == date_str and row.get("Passenger") == person_name:
                flights.append(row)

    if not flights:
        return f"✈️ Для **{person_name}** нет запланированных рейсов на этот день."

    formatted_date = datetime.strptime(date_str, "%Y-%m-%d").strftime("%d.%m.%Y")
    text = f"👤 **РЕЙСЫ ПАССАЖИРА: {person_name.upper()}** ({formatted_date})\n"
    text += "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n\n"

    for f in flights:
        status_icon = "🟢" if f.get('Status') == "По расписанию" else "🟡"
        text += (
            f"{f.get('TimeSlot', '')}\n"
            f"📍 **{f.get('Route', '')}**\n"
            f"✈️ Рейс: {f.get('Airline', '')} ({f.get('Flight', '')})\n"
            f"⏰ Вылет: **{f.get('Departure', '')}** | Прилет: **{f.get('Arrival', '')}**\n"
            f"Статус: {status_icon} {f.get('Status', '')}\n"
            f"{'—'*20}\n"
        )
    return text

def get_full_schedule(date_str):
    """Возвращает полное расписание на весь день (с утра до ночи)"""
    if not os.path.exists(CSV_FILE):
        return "⚠️ Файл с расписанием не найден."

    flights = []
    with open(CSV_FILE, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row.get("Date") == date_str:
                flights.append(row)

    formatted_date = datetime.strptime(date_str, "%Y-%m-%d").strftime("%d.%m.%Y")
    text = f"📋 **ПОЛНОЕ РАСПИСАНИЕ С УТРА ДО НОЧИ** ({formatted_date})\n"
    text += "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n\n"

    current_slot = ""
    for f in flights:
        if f.get("TimeSlot") != current_slot:
            current_slot = f.get("TimeSlot")
            text += f"\n### {current_slot} ###\n"

        status_icon = "🟢" if f.get('Status') == "По расписанию" else "🟡"
        text += (
            f"👤 **{f.get('Passenger', '')}** — {f.get('Route', '')}\n"
            f"✈️ {f.get('Flight', '')} | ⏰ {f.get('Departure', '')} ➔ {f.get('Arrival', '')} ({status_icon})\n"
        )

    return text

def get_main_keyboard(date_str):
    """Клавиатура с кнопками для каждого человека"""
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👤 Сергей", callback_data=f"user_Сергей_{date_str}"),
            InlineKeyboardButton(text="👤 Дарья", callback_data=f"user_Дарья_{date_str}")
        ],
        [
            InlineKeyboardButton(text="👤 Валерия", callback_data=f"user_Валерия_{date_str}"),
            InlineKeyboardButton(text="👤 Максим", callback_data=f"user_Максим_{date_str}")
        ],
        [
            InlineKeyboardButton(text="📋 Показать всё расписание", callback_data=f"full_{date_str}")
        ],
        [
            InlineKeyboardButton(text="📅 На сегодня", callback_data=f"date_{datetime.now().strftime('%Y-%m-%d')}"),
            InlineKeyboardButton(text="📅 На завтра", callback_data=f"date_{(datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')}")
        ]
    ])
    return kb

@dp.message(Command("start"))
@dp.message(Command("flights"))
async def start_handler(message: types.Message):
    today_str = datetime.now().strftime("%Y-%m-%d")
    text = "👋 Выбери, чье расписание ты хочешь посмотреть, или открой весь список на день:"
    await message.answer(text, reply_markup=get_main_keyboard(today_str))

@dp.callback_query(F.data.startswith("user_"))
async def process_user_callback(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    person_name = parts[1]
    date_str = parts[2]
    
    text = get_person_schedule(person_name, date_str)
    await callback.message.edit_text(text, reply_markup=get_main_keyboard(date_str), parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data.startswith("full_"))
async def process_full_callback(callback: types.CallbackQuery):
    date_str = callback.data.split("full_")[1]
    text = get_full_schedule(date_str)
    await callback.message.edit_text(text, reply_markup=get_main_keyboard(date_str), parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data.startswith("date_"))
async def process_date_callback(callback: types.CallbackQuery):
    date_str = callback.data.split("date_")[1]
    text = f"📅 Выбрана дата: **{datetime.strptime(date_str, '%Y-%m-%d').strftime('%d.%m.%Y')}**\n\nВыбери человека ниже:"
    await callback.message.edit_text(text, reply_markup=get_main_keyboard(date_str), parse_mode="Markdown")
    await callback.answer()

async def main():
    print("Бот успешно запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
