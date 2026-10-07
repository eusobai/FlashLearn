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


# =========================
# СТАРТ ТЕСТА С ВЫБОРАМИ
# =========================


async def send_choice_quiz(message: Message, user_id: int):
 
    # Выбираем случайное слово,
    # которое будет правильным ответом.
    question_word = random.choice(WORDS)

    # Запоминаем правильный ответ для этого пользователя.
    #
    # Например:
    # current_choice_quiz_words[123] = question_word
    #
    # Позже обработчик ответа достанет это слово
    # и сравнит его с выбранным пользователем вариантом.
    current_choice_quiz_words[user_id] = question_word

    # Выбираем 3 неправильных слова
    wrong_words = random.sample(
        [item for item in WORDS if item["id"] != question_word["id"]],
        3
    )

    # Объединяем правильный и неправильные ответы
    options = [question_word, *wrong_words]
    
    # Перемешиваем варианты,
    # чтобы правильный ответ каждый раз
    # находился на случайной позиции.
    random.shuffle(options)

    # Создаём кнопки с вариантами    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard = [
            [InlineKeyboardButton(text = options[0]['russian'], callback_data = f"choice:{options[0]['id']}")],
            [InlineKeyboardButton(text = options[1]['russian'], callback_data = f"choice:{options[1]['id']}")],
            [InlineKeyboardButton(text = options[2]['russian'], callback_data = f"choice:{options[2]['id']}")],
            [InlineKeyboardButton(text = options[3]['russian'], callback_data = f"choice:{options[3]['id']}")],
            [InlineKeyboardButton(text = "🛑 Завершить тренировку", callback_data = "finish_quiz")]
        ]
    )

    # Отправляем вопрос и кнопки
    question_message = await message.answer(
        f"📝 Как переводится слово: {question_word['english']}?",
        reply_markup = keyboard
    )

    active_quiz_message[user_id] = question_message


@router.callback_query(F.data == "quiz_choice")
async def start_choice_quiz(callback: CallbackQuery) -> None:

    # Сразу убираем загрузку у нажатой inline-кнопки.
    await safe_callback_answer(callback)

    # Получаем ID пользователя
    user_id = callback.from_user.id

    # Вызываем функцию, чтобы любая новая команда отменяла предыдущую тренировку и убирала её кнопку    
    await cancel_active_quiz(user_id)
    
    # Создаём статистику новой тренировки.
    active_quiz_stats[user_id] = {
        "correct": 0,
        "total": 0,
        "type": "choice"
    }

    logger.info(
        "Choice quiz started | user_id=%s",
        user_id
    )

    
    # Отправляем первый вопрос тренировки.
    await send_choice_quiz(callback.message, user_id)



@router.callback_query(F.data == "finish_quiz")
async def finish_quiz(callback: CallbackQuery) -> None:

    # Сразу убираем загрузку у нажатой inline-кнопки.
    await safe_callback_answer(callback)

    user_id = callback.from_user.id

    # Удаляем статистику текущей тренировки.
    stats = active_quiz_stats.pop(user_id, None)

    # Проверяем, существует ли ещё текущая тренировка.    
    if not stats:
        return

    # Получаем тип текущей тренировки.
    quiz_type = stats["type"] 

    # Получаем общее количество отвеченных вопросов.
    total_questions = stats["total"]
    
    # Получаем количество правильных ответов.
    correct_answers = stats["correct"]

    # Количество ошибок
    wrong_answers = total_questions - correct_answers

    # Вычисляем процент правильных ответов.
    accuracy_percent = (
        round(correct_answers / total_questions * 100)
        if(total_questions)
        else 0 
    )

    logger.info(
        "Quiz finished | user_id=%s | type=%s | total=%s | correct=%s | accuracy=%s%%",
        user_id,
        quiz_type,
        total_questions,
        correct_answers,
        accuracy_percent,
    )

    # Удаляем активный вопрос в зависимости от типа тренировки.
    # потому что тренировка завершена.
    if quiz_type == "choice":
        current_choice_quiz_words.pop(user_id, None)

    elif quiz_type == "text":
        current_quiz_words.pop(user_id, None)

    # Убираем кнопку «Завершить тренировку».
    await hide_active_quiz_keyboard(user_id)

    # Показываем итоговый результат пользователю.
    await callback.message.answer(
        f"🏁 Тренировка завершена!\n\n"
        f"Вопросов: {total_questions}\n"
        f"Правильных: {correct_answers}\n"
        f"Ошибок: {wrong_answers}\n"
        f"Результат: {accuracy_percent}%\n"
    ) 
    