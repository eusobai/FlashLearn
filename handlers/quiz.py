# =========================
# ИМПОРТЫ
# =========================

# 
import random

# Основные классы aiogram.
from aiogram import Router, F

# Типы Telegram-объектов.
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    Message
)

from aiogram.filters import Command

# Обрабатывает ошибки Telegram, например,
# когда пользователь нажимает на устаревшую inline-кнопку.
from aiogram.exceptions import TelegramBadRequest

# Функции для работы с базой данных.
from database.database import get_words

# Безопасно подтверждает нажатие inline-кнопки.
# Это нужно делать сразу, чтобы у пользователя не крутилась загрузка.
from utils.safe_calback import safe_callback_answer


# Логгер проекта для записи информации и ошибок.
from utils.logger import logger

# 
# ROUTER
# 

router = Router()

# Здесь временно хранится текущее слово для каждого пользователя,
# который проходит тест.
#
# current_quiz_words — текстовый тест.
# current_choice_quiz_words — тест с вариантами ответа.
current_quiz_words = {}
current_choice_quiz_words = {}

# Временная статистика активных тренировок: текстовых и с вариантами.
# Например:
# ative_quiz_stats[123] = {
#     "correct": 3,
#     "total": 5
# }
#
# Эта статистика не хранится в БД.
# Она нужна только пока пользователь проходит одну тренировку.
active_quiz_stats = {}

# Хранит последнее сообщение с вопросом тренировки каждого пользователя.
# Нужно, чтобы потом убрать с него кнопку «Завершить тренировку».
active_quiz_message = {}


WORDS = get_words()


# =========================
# ФУНКЦИИ ПОМОШНИКИ
# =========================

async def hide_active_quiz_keyboard(user_id: int) -> None:

    question_message = active_quiz_message.pop(user_id, None)
    
    if question_message is None:
        return
    
    try:
        await question_message.edit_reply_markup(reply_markup = None)

    except TelegramBadRequest as error: 
        logger.warning(
            "Failed to remove training buttons | user_id=%s | error=%s",
            user_id, error
        )


async def cancel_active_quiz(user_id) -> None:

    # Убираем кнопку со старого вопроса.
    await hide_active_quiz_keyboard(user_id)

    # Полностью очищаем временные данные старой тренировки.
    active_quiz_stats.pop(user_id, None)
    current_choice_quiz_words.pop(user_id, None)
    current_quiz_words.pop(user_id, None)


# # =========================
# # НАЧАЛО ТЕСТА
# # =========================

@router.message(Command("quiz"))
@router.message(F.text == "🧠 Тренировка")
async def start_quiz(message: Message) -> None:

    await cancel_active_quiz(message.from_user.id)
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard = [
            [
                InlineKeyboardButton(text = "🎯 Выбор ответа", callback_data = "quiz_choice")
            ],
            [
                InlineKeyboardButton(text = "✍️ Написать ответ", callback_data = "quiz_text")
            ]
        ]
        )

    await message.answer(
        "🧠 Выбери режим тренировки:",
        reply_markup = keyboard
    )



# =========================
#  ТЕСТА С ТЕКСТОМ
# =========================


# Этот обработчик срабатывает,
# когда пользователь нажимает inline-кнопку
# "✍️ Написать ответ".
@router.callback_query(F.data == "quiz_text")
async def start_text_quiz(callback: CallbackQuery) -> None:

    # Сразу убираем загрузку у нажатой inline-кнопки.
    await safe_callback_answer(callback)

    # Получаем Telegram ID пользователя,
    # который нажал кнопку.
    #
    # ID нужен, чтобы сохранить текущее слово
    # именно для этого пользователя.
    user_id = callback.from_user.id
  
    # Вызываем функцию, чтобы любая новая команда отменяла предыдущую тренировку и убирала её кнопку    
    await cancel_active_quiz(user_id)
  
    active_quiz_stats[user_id] = {
        "correct": 0,
        "total": 0,
        "type": "text"
    }

    logger.info(
        "Text quiz started | user_id=%s",
        user_id
    )

    # Выбираем случайное слово из общего словаря.
    question_word = random.choice(WORDS)

    # Сохраняем выбранное слово в словаре current_quiz_words.
    #
    # Ключ:
    # user_id
    #
    # Значение:
    # выбранное слово
    #
    # Например:
    # current_quiz_words[123456] = question_word
    #
    # Благодаря этому после ответа пользователя
    # бот сможет понять, какое слово нужно проверить.
    current_quiz_words[user_id] = question_word

    keyboard = InlineKeyboardMarkup(
        inline_keyboard = [
            [InlineKeyboardButton( text="🛑 Завершить тренировку", callback_data="finish_quiz")]
        ]
    )


    # Отправляем пользователю вопрос.
    #
    # Пользователь должен самостоятельно
    # написать перевод слова.
    question_message = await callback.message.answer(
        f"📝 Как переводится слово: {question_word['english']}?\n\n",
        reply_markup = keyboard
    )

    active_quiz_message[user_id] = question_message

