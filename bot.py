import asyncio
import csv
import os

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.client.session.aiohttp import AiohttpSession

BOT_TOKEN = "8772614838:AAFMOZLj2CLrdoiE0KVPS0Mff_S1u0mnxiM"
CSV_FILE = "schedule.csv"

# Настройка прокси для бесплатного тарифа PythonAnywhere
session = AiohttpSession(proxy="http://proxy.server:3128")
bot = Bot(token=BOT_TOKEN, session=session)
dp = Dispatcher()

def init_csv():
    # Создаем/перезаписываем файл с расписанием всех рейсов
    rows = [
        ["Passenger", "Route", "Airline", "Flight", "Departure", "Arrival", "Status"],
        ["Сергей", "Москва / СПб → Лондон", "British Airways", "BA-879", "09:30", "14:15", "По расписанию"],
        ["Дарья", "Москва / СПб → Корфу", "Aegean Airlines", "A3-402", "11:20", "15:45", "По расписанию"],
        ["Валерия", "Москва / СПб → Бангкок", "Qatar Airways", "QR-338", "18:00", "07:30 (+1)", "По расписанию"],
        ["Максим", "Москва / Краснодар → Бангкок", "Aeroflot", "SU-270", "22:10", "11:00 (+1)", "Задерживается"]
    ]
    with open(CSV_FILE, mode="w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerows(rows)

# При запуске проверяем или создаем актуальный CSV
init_csv()

def get_flights_text():
    if not os.path.exists(CSV_FILE):
        return "⚠️ Файл с расписанием не найден."

    flights = []
    with open(CSV_FILE, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            flights.append(row)

    if not flights:
        return "✈️ На данный момент доступных рейсов нет."

    text = "🛫 **Актуальное расписание всех пассажиров:**\n\n"
    for f in flights:
        status_icon = "🟢" if f.get('Status') == "По расписанию" else "🟡"
        text += (
            f"👤 **{f.get('Passenger', '')}**\n"
            f"📍 Маршрут: **{f.get('Route', '')}**\n"
            f"✈️ Рейс: {f.get('Airline', '')} ({f.get('Flight', '')})\n"
            f"⏰ Вылет: {f.get('Departure', '')} | Прилет: {f.get('Arrival', '')}\n"
            f"Статус: {status_icon} {f.get('Status', '')}\n"
            f"{'—'*25}\n"
        )
    return text

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Обновить расписание", callback_data="refresh_flights")]
    ])
    await message.answer(
        f"Привет, {message.from_user.first_name}! 👋\n\n"
        "Я бот для отслеживания персональных авиарейсов.\n"
        "Нажми кнопку ниже или напиши /flights, чтобы узнать расписание.",
        reply_markup=kb,
        parse_mode="Markdown"
    )

@dp.message(Command("flights"))
async def flights_command_handler(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Обновить", callback_data="refresh_flights")]
    ])
    await message.answer(get_flights_text(), reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(F.data == "refresh_flights")
async def refresh_callback_handler(callback: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Обновить", callback_data="refresh_flights")]
    ])
    try:
        await callback.message.edit_text(get_flights_text(), reply_markup=kb, parse_mode="Markdown")
        await callback.answer("Расписание обновлено!")
    except Exception:
        await callback.answer("Расписание уже актуально.")

async def main():
    print("Бот успешно запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
