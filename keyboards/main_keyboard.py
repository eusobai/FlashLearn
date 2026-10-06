# Типы Telegram-объектов:
# KeyboardButton и ReplyKeyboardMarkup — обычная клавиатура,
from aiogram.types import (

    KeyboardButton,
    ReplyKeyboardMarkup,

)

# Это обычная клавиатура Telegram.
# Её кнопки отправляют боту обычный текст.
main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📚 Учить слова")],
        [KeyboardButton(text="🧠 Тренировка")],
        [KeyboardButton(text="📊 Моя статистика")],
        [KeyboardButton(text="⭐ Мои слова")],
        [KeyboardButton(text="❓ Помощь")],
    ],
    resize_keyboard=True,
    input_field_placeholder="Выбери действие",
)
