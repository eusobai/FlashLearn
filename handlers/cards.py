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
    CallbackQuery,
    InlineKeyboardMarkup, 
    InlineKeyboardButton
)

# 
from utils.safe_calback import safe_callback_answer

# Функция для управления активной тренировкой.
from utils.quiz_utils import cancel_active_quiz

from utils.logger import logger

# Функции для работы с базой данных.
from database.database import (
    get_words, 
    get_levels_from_db, 
    get_user_level_in_db, 
    set_user_level
)
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



# =========================
# ОБУЧЕНИЕ: ВЫБОР УРОВНЯ
# =========================

# Точка входа в обучение: сюда ведут и команда /card, и кнопка «📚 Учить слова».
# Решает, какой экран показать: выбор уровня (если он ещё не задан) или следующий шаг.
@router.message(Command("card"))
@router.message(F.text == "📚 Учить слова")
async def open_learning(message: Message) -> None:

    user_id = message.from_user.id
    await cancel_active_quiz(user_id)

    # None означает, что пользователь ещё не выбирал уровень.
    user_level = get_user_level_in_db(user_id)
    
    if user_level is None:

        levels = get_levels_from_db()
        
        level_keyboard = build_level_keyboard(levels)

        await message.answer("🎓 Укажите ваш уровень английского: ", reply_markup=level_keyboard)
    else:
        await message.answer(

        # Заглушка: здесь будет экран выбора режима (случайные слова / по темам).
        "Выбери темы, по которым хочешь учить слова.")



# Пользователь нажал кнопку с уровнем. В callback_data лежит "level:<id>".
@router.callback_query(F.data.startswith("level:"))
async def select_level(callback: CallbackQuery):
    
    await safe_callback_answer(callback)

    user_id = callback.from_user.id
    level_id = int(callback.data.split(":", 1)[1])
    set_user_level(user_id, level_id)

    # Убираем кнопки, чтобы уровень нельзя было выбрать повторно по старому сообщению.
    await callback.message.edit_reply_markup(reply_markup=None)
    
    await callback.message.answer(
        "Уровень сохранён ✅ \n\n"
        "Выбери темы, по которым хочешь учить слова.")


# Кнопка «Узнать свой уровень».
@router.callback_query(F.data == "check_level")
async def start_level_test(callback: CallbackQuery) -> None:
    await safe_callback_answer(callback)
    
    await callback.message.edit_reply_markup(reply_markup=None)

    # Заглушка: тест уровня ещё не реализован.
    await callback.message.answer(
        "Скоро здесь будет тест для определения уровня.",
        reply_markup=None
    )

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
