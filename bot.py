import sqlite3
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import datetime, timedelta

TOKEN = "7954619967:AAE3uSKyzofUVjLCCToKICiURxbRgXpXov8"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Подключение к базе данных
conn = sqlite3.connect("weekends.db")
cursor = conn.cursor()
cursor.execute(
    """CREATE TABLE IF NOT EXISTS weekends (
        user_id INTEGER,
        date TEXT
    )"""
)
conn.commit()


# Добавление выходных
@dp.message(Command("add"))
async def add_weekend(message: types.Message):
    keyboard = InlineKeyboardBuilder()
    today = datetime.today()

    for i in range(30):  # Показываем 30 дней вперед
        date = today + timedelta(days=i)
        keyboard.button(text=date.strftime("%d.%m"), callback_data=f"date_{date.strftime('%Y-%m-%d')}")

    await message.answer("Выберите дату выходного:", reply_markup=keyboard.as_markup())


# Обработчик выбора даты
@dp.callback_query(lambda c: c.data.startswith("date_"))
async def process_date(callback_query: types.CallbackQuery):
    date = callback_query.data.split("_")[1]
    user_id = callback_query.from_user.id

    cursor.execute("INSERT INTO weekends (user_id, date) VALUES (?, ?)", (user_id, date))
    conn.commit()

    await callback_query.answer(f"Добавлено: {date}", show_alert=True)


# Просмотр всех совпадающих дат
@dp.message(Command("matches"))
async def get_matches(message: types.Message):
    cursor.execute("SELECT date, COUNT(user_id) FROM weekends GROUP BY date ORDER BY COUNT(user_id) DESC")
    results = cursor.fetchall()

    if results:
        response = "Совпадающие даты:\n" + "\n".join(f"{date}: {count} чел." for date, count in results)
    else:
        response = "Нет совпадающих дат."

    await message.answer(response)


# Просмотр своих выходных
@dp.message(Command("mydates"))
async def my_dates(message: types.Message):
    user_id = message.from_user.id
    cursor.execute("SELECT date FROM weekends WHERE user_id = ?", (user_id,))
    results = cursor.fetchall()

    if results:
        response = "Ваши выходные:\n" + "\n".join(date[0] for date in results)
    else:
        response = "Вы не добавили ни одной даты."

    await message.answer(response)


# Удаление выходных (выбор одной или всех)
@dp.message(Command("remove"))
async def remove_date(message: types.Message):
    user_id = message.from_user.id
    cursor.execute("SELECT date FROM weekends WHERE user_id = ?", (user_id,))
    results = cursor.fetchall()

    if not results:
        await message.answer("У вас нет добавленных выходных.")
        return

    keyboard = InlineKeyboardBuilder()
    for date in results:
        keyboard.button(text=date[0], callback_data=f"remove_{date[0]}")
    
    keyboard.button(text="❌ Удалить все", callback_data="remove_all")

    await message.answer("Выберите дату для удаления или удалите все сразу:", reply_markup=keyboard.as_markup())


# Обработчик удаления одной даты
@dp.callback_query(lambda c: c.data.startswith("remove_"))
async def process_remove(callback_query: types.CallbackQuery):
    date = callback_query.data.split("_")[1]
    user_id = callback_query.from_user.id

    cursor.execute("DELETE FROM weekends WHERE user_id = ? AND date = ?", (user_id, date))
    conn.commit()

    await callback_query.answer(f"Удалено: {date}", show_alert=True)


# Обработчик удаления всех дат
@dp.callback_query(lambda c: c.data == "remove_all")
async def process_remove_all(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id

    cursor.execute("DELETE FROM weekends WHERE user_id = ?", (user_id,))
    conn.commit()

    await callback_query.answer("Все ваши выходные удалены.", show_alert=True)


# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
