# =========================
# ИМПОРТЫ
# =========================

import random

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

# 
from utils.message_utils import clear_old_buttons

# Функция для управления активной тренировкой.
from utils.quiz_utils import cancel_active_quiz

from utils.logger import logger

# Функции для работы с базой данных.
from database.database import (
    get_words, 
    get_levels_from_db,
    get_words_by_level_in_db,
    get_words_by_topic_in_db, 
    get_user_level_in_db, 
    set_user_level,
    get_topics_in_db
)
# Кнопки для проверки уровни
from keyboards.cards_keyboard import build_level_keyboard, build_mode_keyboard, build_topic_keyboard

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

    # Сразу убираем загрузку у нажатой inline-кнопки.
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
        "Выбери режим, по которым хочешь учить слова.", reply_markup=build_mode_keyboard())



# Пользователь нажал кнопку с уровнем. В callback_data лежит "level:<id>".
@router.callback_query(F.data.startswith("level:"))
async def select_level(callback: CallbackQuery):

    # Сразу убираем загрузку у нажатой inline-кнопки.
    await safe_callback_answer(callback)

    user_id = callback.from_user.id
    level_id = int(callback.data.split(":", 1)[1])
    
    set_user_level(user_id, level_id)

    # Убираем кнопки, чтобы уровень нельзя было выбрать повторно по старому сообщению.
    await callback.message.edit_reply_markup(reply_markup=None)
    
    await callback.message.answer(
        "Уровень сохранён ✅ \n\n"
        "Выбери режим, по которым хочешь учить слова.", reply_markup=build_mode_keyboard())


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


# Отправляет карточку слова: текст и кнопка «В избранное».
# word — словарь с данными слова (id, english, russian, ...).
async def send_card(message: Message, word: dict, username: str, next_data: str):

    logger.info("Card sent | username=%s | word=%s", username, word["english"])

    # Создаём inline-кнопку.
    #
    # text — текст, который видит пользователь.
    #
    # callback_data — данные, которые получит бот
    # после нажатия кнопки.
    #
    # Например:
    # favourite:85
    #
    # Благодаря этому бот знает,
    # какое слово нужно добавить в избранное.
    favourite_button = InlineKeyboardButton(
        text = "⭐ Добавить в мои слова", callback_data=f"favourite:{word['id']}"
    )


    next_button = InlineKeyboardButton(text="➡️ Следующее слово", callback_data=next_data)
    # Создаём inline-клавиатуру и помещаем кнопку в неё.
    favorite_keyboard = InlineKeyboardMarkup(inline_keyboard=[ [favourite_button], [next_button] ])

    # Отправляем карточку и прикрепляем inline-кнопку.
    await message.answer(
        f"📚 Слово: <b>{word['english']}</b>\n"
        f"RU Перевод: {word['russian']}\n"
        f"📖 Определение: {word['definition']}\n"
        f"💬 Пример: {word['example']}\n"
        f"🔊 Произношение: {word['pronunciation']}",
        reply_markup=favorite_keyboard,
        parse_mode = "HTML"
    )


# Режим «🎲 Любые слова»: случайное слово из всего словаря, без учёта уровня.
@router.callback_query(F.data == "random_words")
async def send_random_word(callback: CallbackQuery) -> None:

    # Убираем анимацию загрузки и удаляем все inline-кнопки, кроме «Добавить в мои слова.
    await safe_callback_answer(callback)
    await clear_old_buttons(callback.message)

    # Вызываем функцию, чтобы любая новая команда отменяла предыдущую тренировку и убирала её кнопку    
    await cancel_active_quiz(callback.from_user.id)
    
    # Выбираем случайное слово из словаря.
    word = random.choice(WORDS)
    await send_card(callback.message, word, callback.from_user.username, "random_words")


@router.callback_query(F.data == "topic_words")
async def select_topic(callback: CallbackQuery) -> None:
    await safe_callback_answer(callback)

    topics = get_topics_in_db()

    await callback.message.answer("🌟 Выбирай темы и начнём учить слова", reply_markup=build_topic_keyboard(topics))


# Режим «🎓 Слова по темам».
@router.callback_query(F.data.startswith("topic:"))
async def get_topic_words(callback: CallbackQuery) -> None:

    # Сразу убираем загрузку у нажатой inline-кнопки.
    await safe_callback_answer(callback)
    await clear_old_buttons(callback.message)
    
    topic_id = int(callback.data.split(":", 1)[1])
    
    topic_words = get_words_by_topic_in_db(topic_id)
    random_word = random.choice(topic_words)
    
    await send_card(callback.message, random_word, callback.from_user.username, f"topic:{topic_id}")

# Режим «🎓 Случайные слова по уровню»: слово подбирается под уровень пользователя.
@router.callback_query(F.data == "random_words_by_level")
async def get_random_level_words(callback: CallbackQuery) -> None:
  
    # Убираем анимацию загрузки и удаляем все inline-кнопки, кроме «Добавить в мои слова.
    await safe_callback_answer(callback)
    await clear_old_buttons(callback.message)

    user_id = callback.from_user.id

    # Вызываем функцию, чтобы любая новая команда отменяла предыдущую тренировку и убирала её кнопку    
    await cancel_active_quiz(user_id)


    user_level = get_user_level_in_db(user_id)

    if user_level is None:
        levels = get_levels_from_db()
        
        level_keyboard = build_level_keyboard(levels)

        await callback.message.answer("🎓 Укажите ваш уровень английского: ", reply_markup=level_keyboard)
        return
    
    words_by_level = get_words_by_level_in_db(user_level)

    if not words_by_level:
        await callback.message.answer("Для этого уровня пока нет слов.")
        return
    
    random_word = random.choice(words_by_level)

    await send_card(callback.message, random_word, callback.from_user.username, "random_words_by_level")

