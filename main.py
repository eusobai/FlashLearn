# =========================
# ИМПОРТЫ
# =========================

import os
import asyncio

# from MODULES
from utils.logger import logger

from handlers.quiz import (
    current_quiz_words, 
    current_choice_quiz_words,
    active_quiz_stats,
    active_quiz_message,
    hide_active_quiz_keyboard,
    cancel_active_quiz
)

# HANDLERS
from handlers import (
    start, 
    help, 
    cards, 
    favourites,
    quiz,
    stats
)

# Основные классы aiogram для создания бота и диспетчера.
from aiogram import Bot, Dispatcher, F

# Фильтры для команд Telegram.
from aiogram.filters import CommandStart, Command

# Типы Telegram-объектов:
# Message — обычное сообщение,
# BotCommand — команда бота,
# KeyboardButton и ReplyKeyboardMarkup — обычная клавиатура,
# InlineKeyboardButton и InlineKeyboardMarkup — inline-кнопки,
# CallbackQuery — нажатие inline-кнопки.
from aiogram.types import (
    BotCommand,
    CallbackQuery,
)

# Обрабатывает ошибку Telegram, когда пользователь нажал старую кнопку
# и Telegram уже не принимает ответ на это нажатие.
from aiogram.exceptions import TelegramBadRequest

# Функции для работы с базой данных.
from database.database import (
    get_words,
    add_user_to_db,
    get_stats_from_db,
    update_stats_in_db,
    reset_stats_in_db,
    add_fav_word_to_db,
    get_fav_words_in_db,
    delete_fav_word_in_db
)

# Загружает переменные из .env.
from dotenv import load_dotenv

# =========================
# НАСТРОЙКА ОКРУЖЕНИЯ
# =========================

# Загружаем данные из файла .env.
# В нашем случае оттуда берётся BOT_TOKEN.
load_dotenv()


# =========================
# НАСТРОЙКА BOT TOKEN
# =========================


# Получаем токен бота из .env.
BOT_TOKEN = os.getenv("TEST_BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("Не найден BOT_TOKEN. Добавь его в файл .env")


# Создаём объект бота и диспетчер.
bot = Bot(token = BOT_TOKEN)
dp = Dispatcher()


# =========================
# /START
# =========================
dp.include_router(start.router)


# =========================
# /HELP
# =========================
dp.include_router(help.router)


# =========================
# КАРТОЧКА
# =========================
dp.include_router(cards.router)


# # =========================
# #  ИЗБРАННЫЕ СЛОВА
# # =========================
dp.include_router(favourites.router)


# # =========================
# # ТЕСТ
# # =========================
dp.include_router(quiz.router)


# =========================
# СТАТИСТИКА
# =========================
dp.include_router(stats.router)

# # =========================
# # СБРОС СТАТИСТИКИ
# # =========================


# @dp.message(Command("reset_stats"))
# async def reset_user_stats(message: Message) -> None:

#     # Вызываем функцию, чтобы любая новая команда отменяла предыдущую тренировку и убирала её кнопку    
#     await cancel_active_quiz(message.from_user.id)
    
#     # Определяем, статистику какого пользователя нужно сбросить.
#     user_id = message.from_user.id

#     # Передаём ID пользователя в функцию БД.
#     reset_stats_in_db(user_id)

#     logger.info("The user statistics have been reset. | user_id=%s", user_id)

#     await message.answer("Твоя статистика успешно сброшена!")


# # =========================
# # ПРОВЕРКА ОТВЕТА НА ТЕСТ
# # =========================


# @dp.message(F.text)
# async def handle_text_answer(message: Message) -> None:
#     user_id = message.from_user.id

#     # Получаем текст ответа пользователя.
#     # strip() убирает пробелы по краям.
#     text = message.text.strip()

#     # Проверяем, есть ли у пользователя активный вопрос.
#     if user_id in current_quiz_words:

#         # Получаем слово, которое пользователь должен был перевести,
#         # и сразу удаляем его из текущего теста.
#         correct_word = current_quiz_words.pop(user_id)
        
#         # Ответ получен - кнопка завершения на старом вопросе больше не нужна.
#         await hide_active_quiz_keyboard(user_id)
        
#         # В БД может быть несколько переводов:
#         #
#         # "завод, фабрика"
#         #
#         # split(";") разделяет их на отдельные варианты.
#         #
#         # strip() убирает пробелы.
#         # lower() приводит всё к нижнему регистру.
#         correct_answers = [
#             answer.strip().lower() for answer in correct_word["russian"].split(";")
#         ]

#         # Проверяем, находится ли ответ пользователя
#         # среди допустимых переводов.
#         is_correct = text.lower() in correct_answers

#         # Обновляем статистику текущей тренировки.
#         active_quiz_stats[user_id]["total"] += 1
        
#         # Обновляем статистику пользователя в БД.
#         update_stats_in_db(user_id, is_correct)

#         logger.info(
#             "Quiz answered | user_id=%s | correct=%s",
#             user_id,
#             is_correct,
#         )

#         # Если пользователь ответил правильно.
#         if is_correct:
#             # Находим все правильные варианты,
#             # кроме того, который уже написал пользователь.
#             active_quiz_stats[user_id]["correct"] += 1

#             other_answers = [
#                 answer for answer in correct_answers 
#                 if answer != text.lower()
#             ]

#             # Если есть другие допустимые переводы,
#             # показываем их пользователю.
#             if other_answers:
#                 await message.answer(
#                     "✅ Правильно!\n\n" f"Другие варианты: {', '.join(other_answers)}"
#                 )
#             else:
#                 await message.answer("✅ Правильно! Молодец.")
                
#         # Если ответ неправильный.
#         else:
#             await message.answer(
#                 "❌ Неправильно.\n\n" f"Правильные ответы: {', '.join(correct_answers)}"
#             )

#         # Сюда будем записывать следующее слово для следующего вопроса.
#         next_word = None

#         # Если это обычная текстовая тренировка,
#         # берём следующее слово из общего списка WORDS.
#         if (active_quiz_stats[user_id]["type"] == "text"):
#             next_word = random.choice(WORDS)

#         # Если это текстовая тренировка только из избранных слов,
#         # берём следующее слово только из избранных слов пользователя.
#         elif (active_quiz_stats[user_id]["type"] == "favourite_text"):
#             next_word = random.choice(get_fav_words_in_db(user_id))    

#         # Сохраняем выбранное слово как текущее слово для следующего ответа пользователя.
#         current_quiz_words[user_id] = next_word

#         keyboard = InlineKeyboardMarkup(
#             inline_keyboard = [
#                 [InlineKeyboardButton(text="🛑 Завершить тренировку", callback_data="finish_quiz")]
#             ]
#         )

#         question_message = await message.answer(
#             f"📝 Как переводится слово: {next_word['english']}?",
#             reply_markup = keyboard
#         )
#         active_quiz_message[user_id] = question_message
#         # Останавливаем обработчик
#         return

#     # Если пользователь не отвечает на активный тест,
#     # бот сообщает, что не знает, что делать с сообщением.
#     await message.answer(
#         "Не понял сообщение. Выбери действие на клавиатуре или используй /start."
#     )

# =========================
# ЗАПУСК БОТА
# =========================


async def main() -> None:
    
    # Регистрируем команды, которые Telegram
    # будет показывать пользователю.
    await bot.set_my_commands(
        [
            BotCommand(command="start", description="Запустить бота"),
            BotCommand(command="card", description="Получить случайное слово"),
            BotCommand(command="quiz", description="Тренировка случайных слов"),
            BotCommand(command="stats", description="Посмотреть статистику"),
            BotCommand(command="favourites", description="Посмотреть мои слова"),
            BotCommand(command='help', description='Помощь по боту')   
        ]
    )

    logger.info("Bot запустился")

    # Запускаем бота и начинаем получать сообщения
    # от Telegram.
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
