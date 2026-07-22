import asyncio
import csv
import os

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

BOT_TOKEN = "8772614838:AAFMOZLj2CLrdoiE0KVPS0Mff_S1u0mnxiM"
CSV_FILE = "schedule.csv"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Создаем базовый CSV с расписанием, если его нет
if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, mode="w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Route", "Airline", "Flight", "Departure", "Arrival", "Status"])
        writer.writerow(["Москва - Сочи", "Аэрофлот", "SU-112", "10:00", "13:30", "По расписанию"])
        writer.writerow(["СПб - Москва", "S7 Airlines", "S7-1020", "12:15", "13:45", "Задерживается"])
        writer.writerow(["Москва - Стамбул", "Turkish Airlines", "TK-414", "15:00", "20:00", "По расписанию"])

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

    text = "🛫 **Актуальное расписание рейсов:**\n\n"
    for f in flights:
        status_icon = "🟢" if f.get('Status') == "По расписанию" else "🟡"
        text += (
            f"📍 **{f.get('Route', '')}**\n"
            f"✈️ Авиакомпания: {f.get('Airline', '')} ({f.get('Flight', '')})\n"
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
        "Я бот для отслеживания авиарейсов.\n"
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
