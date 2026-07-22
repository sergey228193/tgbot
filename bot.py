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

# Настройка прокси для PythonAnywhere
session = AiohttpSession(proxy="http://proxy.server:3128")
bot = Bot(token=BOT_TOKEN, session=session)
dp = Dispatcher()

# Базовые данные пассажиров и их рейсов
PASSENGERS_DATA = [
    {"name": "Сергей", "route": "Москва / СПб → Лондон", "airline": "British Airways", "flight": "BA-879", "dep": "09:30", "arr": "14:15"},
    {"name": "Дарья", "route": "Москва / СПб → Корфу", "airline": "Aegean Airlines", "flight": "A3-402", "dep": "11:20", "arr": "15:45"},
    {"name": "Валерия", "route": "Москва / СПб → Бангкок", "airline": "Qatar Airways", "flight": "QR-338", "dep": "18:00", "arr": "07:30 (+1)"},
    {"name": "Максим", "route": "Москва / Краснодар → Бангкок", "airline": "Aeroflot", "flight": "SU-270", "dep": "22:10", "arr": "11:00 (+1)"},
]

def init_monthly_csv():
    """Генерирует расписание на 30 дней вперед и сохраняет в CSV"""
    rows = [["Date", "Passenger", "Route", "Airline", "Flight", "Departure", "Arrival", "Status"]]
    
    today = datetime.now().date()
    
    for i in range(30):
        current_date = (today + timedelta(days=i)).strftime("%Y-%m-%d")
        
        for p in PASSENGERS_DATA:
            # Для примера: случайная легкая задержка на некоторые дни
            status = "Задерживается" if (i % 7 == 3 and p["name"] == "Максим") else "По расписанию"
            
            rows.append([
                current_date,
                p["name"],
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
    print("📅 Файл расписания на месяц успешно обновлен!")

# Создаем файл с расписанием на месяц при запуске
init_monthly_csv()

def get_flights_by_date(target_date_str):
    """Считывает из CSV рейсы на конкретную дату (ГГГГ-ММ-ДД)"""
    if not os.path.exists(CSV_FILE):
        return "⚠️ Файл с расписанием не найден."

    flights = []
    with open(CSV_FILE, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row.get("Date") == target_date_str:
                flights.append(row)

    if not flights:
        return f"✈️ На дату **{target_date_str}** рейсов не найдено."

    # Красивое форматирование даты
    formatted_date = datetime.strptime(target_date_str, "%Y-%m-%d").strftime("%d.%m.%Y")
    
    text = f"🛫 **РАСПИСАНИЕ РЕЙСОВ НА {formatted_date}:**\n"
    text += "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n\n"

    for f in flights:
        status_icon = "🟢" if f.get('Status') == "По расписанию" else "🟡"
        text += (
            f"👤 **{f.get('Passenger', '')}**\n"
            f"📍 Маршрут: {f.get('Route', '')}\n"
            f"✈️ Рейс: {f.get('Airline', '')} ({f.get('Flight', '')})\n"
            f"⏰ Вылет: {f.get('Departure', '')} | Прилет: {f.get('Arrival', '')}\n"
            f"Статус: {status_icon} {f.get('Status', '')}\n\n"
        )

    return text

def get_main_keyboard():
    """Клавиатура с выбором даты"""
    today_str = datetime.now().strftime("%Y-%m-%d")
    tomorrow_str = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📅 Сегодня", callback_data=f"date_{today_str}"),
            InlineKeyboardButton(text="📅 Завтра", callback_data=f"date_{tomorrow_str}")
        ],
        [
            InlineKeyboardButton(text="🗓 Посмотреть дни на неделю", callback_data="show_week")
        ]
    ])
    return kb

@dp.message(Command("start"))
@dp.message(Command("flights"))
async def start_handler(message: types.Message):
    today_str = datetime.now().strftime("%Y-%m-%d")
    text = get_flights_by_date(today_str)
    await message.answer(text, reply_markup=get_main_keyboard(), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("date_"))
async def process_date_callback(callback: types.CallbackQuery):
    target_date = callback.data.split("date_")[1]
    text = get_flights_by_date(target_date)
    
    try:
        await callback.message.edit_text(text, reply_markup=get_main_keyboard(), parse_mode="Markdown")
        await callback.answer()
    except Exception:
        await callback.answer("Уже показано актуальное расписание.")

@dp.callback_query(F.data == "show_week")
async def show_week_buttons(callback: types.CallbackQuery):
    """Показывает кнопки на ближайшие 7 дней"""
    today = datetime.now().date()
    buttons = []
    
    for i in range(7):
        day_date = today + timedelta(days=i)
        date_str = day_date.strftime("%Y-%m-%d")
        display_str = day_date.strftime("%d.%m (%a)")
        buttons.append([InlineKeyboardButton(text=f"✈️ {display_str}", callback_data=f"date_{date_str}")])
        
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data=f"date_{today.strftime('%Y-%m-%d')}")])
    
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text("Выбери нужный день из списка:", reply_markup=kb)
    await callback.answer()

async def main():
    print("Бот успешно запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
