# =========================
# ИМПОРТЫ
# =========================

# 
import random

# Типы Telegram-объектов.
from aiogram.types import (
    CallbackQuery, 
    Message, 
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

# Функции для работы с базой данных.
from database.database import ( 
    get_fav_words_in_db,
    
)

#  Здесь временно хранится текущее слово, статистика, вопрос для каждого пользователя,
from handlers.quiz import (
    active_quiz_message,
    current_choice_quiz_words
)


async def send_fav_choice_quiz(message: Message, user_id: int):

    favourite_words = get_fav_words_in_db(user_id)

    # Для теста с вариантами нужно минимум 2 слова.
    if (len(favourite_words) < 2):
        await message.answer("⭐ Для тренировки с вариантами нужно минимум 2 избранных слова.")
        return

    question_word = random.choice(favourite_words)

    # Запоминаем правильный ответ для этого пользователя.
    #
    # Например:
    # current_choice_quiz_words[123] = question_word
    #
    # Позже обработчик ответа достанет это слово
    # и сравнит его с выбранным пользователем вариантом.
    current_choice_quiz_words[user_id] = question_word

    wrong_answers = [
        item 
        for item in favourite_words 
        if item["id"] != question_word["id"] 
    ]

    # Нам нужно максимум 3 неправильных ответа.
    wrong_answers = wrong_answers[:3]

    options = [question_word, *wrong_answers]

    random.shuffle(options)
    
    buttons = []

    for option in options:
        buttons.append(
            [
                InlineKeyboardButton(text = option["russian"], callback_data = f"choice:{option['id']}")
            ]
        )
    buttons.append(
        [
            InlineKeyboardButton(
                text = "🛑 Завершить тренировку", 
                callback_data = "finish_quiz"
            )
        ]
    )
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard = buttons
    )

    question_message = await message.answer(
        f"📝 Как переводится слово: {question_word['english']}?",
        reply_markup = keyboard
    )

    active_quiz_message[user_id] = question_message 

