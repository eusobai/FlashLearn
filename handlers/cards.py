# =========================
# ИМПОРТЫ
# =========================


# Основные классы aiogram.
from aiogram import Router, F

# Фильтры Telegram-команд.
from aiogram.filters import Command

# Типы Telegram-объектов.
from aiogram.types import (
    Message, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton
)

# Функция для управления активной тренировкой.
from utils.quiz_utils import cancel_active_quiz

from utils.logger import logger

# Функции для работы с базой данных.
from database.database import get_words, get_levels_from_db

# Кнопки для проверки уровни
from keyboards.cards_keyboard import build_level_keyboard

# =========================
# ROUTER
# =========================
router = Router()

# =========================
# ЗАГРУЗКА СЛОВАРЯ
# =========================
WORDS = get_words()


@router.message(Command("card"))
@router.message(F.text == "📚 Учить слова")
async def show_level_choice(message: Message) -> None:
    
    levels = get_levels_from_db()
    keyboard = build_level_keyboard(levels)

    await message.answer("🎓 Укажите ваш уровень английского: ", reply_markup=keyboard)


# async def send_card(message: Message) -> None:

#     # Вызываем функцию, чтобы любая новая команда отменяла предыдущую тренировку и убирала её кнопку    
#     await cancel_active_quiz(message.from_user.id)
    
#     # Выбираем случайное слово из словаря.
#     word = random.choice(WORDS)

#     username = message.from_user.username if message.from_user.username else "unknown"

#     logger.info("Card sent | username=%s | word=%s", username, word["english"])

#     # Создаём inline-кнопку.
#     #
#     # text — текст, который видит пользователь.
#     #
#     # callback_data — данные, которые получит бот
#     # после нажатия кнопки.
#     #
#     # Например:
#     # favourite:85
#     #
#     # Благодаря этому бот знает,
#     # какое слово нужно добавить в избранное.
#     favourite_button = InlineKeyboardButton(
#         text = "⭐ Добавить в мои слова", callback_data=f"favourite:{word['id']}"
#     )

#     # Создаём inline-клавиатуру и помещаем кнопку в неё.
#     favorite_keyboard = InlineKeyboardMarkup(inline_keyboard=[[favourite_button]])

#     # Отправляем карточку и прикрепляем inline-кнопку.
#     await message.answer(
#         f"📚 Слово: <b>{word['english']}</b>\n"
#         f"RU Перевод: {word['russian']}\n"
#         f"📖 Определение: {word['definition']}\n"
#         f"💬 Пример: {word['example']}\n"
#         f"🔊 Произношение: {word['pronunciation']}",
#         reply_markup=favorite_keyboard,
#         parse_mode = "HTML"
#     )
