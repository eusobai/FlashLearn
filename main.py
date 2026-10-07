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
from handlers import start, help, cards, favourites


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




#

# # =========================
# # НАЧАЛО ТЕСТА
# # =========================


# @dp.message(Command("quiz"))
# @dp.message(F.text == "🧠 Тренировка")
# async def start_quiz(message: Message) -> None:

#     await cancel_active_quiz(message.from_user.id)
    
#     keyboard = InlineKeyboardMarkup(
#         inline_keyboard = [
#             [
#                 InlineKeyboardButton(text = "🎯 Выбор ответа", callback_data = "quiz_choice")
#             ],
#             [
#                 InlineKeyboardButton(text = "✍️ Написать ответ", callback_data = "quiz_text")
#             ]
#         ]
#         )

#     await message.answer(
#         "🧠 Выбери режим тренировки:",
#         reply_markup = keyboard
#     )

# # =========================
# # СТАРТ ТЕКСТОВОГО ТЕСТА
# # =========================

# # Этот обработчик срабатывает,
# # когда пользователь нажимает inline-кнопку
# # "✍️ Написать ответ".
# @dp.callback_query(F.data == "quiz_text")
# async def start_text_quiz(callback: CallbackQuery) -> None:

#     # Сразу убираем загрузку у нажатой inline-кнопки.
#     await safe_callback_answer(callback)

#     # Получаем Telegram ID пользователя,
#     # который нажал кнопку.
#     #
#     # ID нужен, чтобы сохранить текущее слово
#     # именно для этого пользователя.
#     user_id = callback.from_user.id
  
#     # Вызываем функцию, чтобы любая новая команда отменяла предыдущую тренировку и убирала её кнопку    
#     await cancel_active_quiz(user_id)
  
#     active_quiz_stats[user_id] = {
#         "correct": 0,
#         "total": 0,
#         "type": "text"
#     }

#     logger.info(
#         "Text quiz started | user_id=%s",
#         user_id
#     )

#     # Выбираем случайное слово из общего словаря.
#     question_word = random.choice(WORDS)

#     # Сохраняем выбранное слово в словаре current_quiz_words.
#     #
#     # Ключ:
#     # user_id
#     #
#     # Значение:
#     # выбранное слово
#     #
#     # Например:
#     # current_quiz_words[123456] = question_word
#     #
#     # Благодаря этому после ответа пользователя
#     # бот сможет понять, какое слово нужно проверить.
#     current_quiz_words[user_id] = question_word

#     keyboard = InlineKeyboardMarkup(
#         inline_keyboard = [
#             [InlineKeyboardButton( text="🛑 Завершить тренировку", callback_data="finish_quiz")]
#         ]
#     )


#     # Отправляем пользователю вопрос.
#     #
#     # Пользователь должен самостоятельно
#     # написать перевод слова.
#     question_message = await callback.message.answer(
#         f"📝 Как переводится слово: {question_word['english']}?\n\n",
#         reply_markup = keyboard
#     )

#     active_quiz_message[user_id] = question_message


# # =========================
# # СТАРТ ТЕСТА С ВЫБОРАМИ
# # =========================

# async def send_choice_quiz(message: Message, user_id: int):
 
#     # Выбираем случайное слово,
#     # которое будет правильным ответом.
#     question_word = random.choice(WORDS)

#     # Запоминаем правильный ответ для этого пользователя.
#     #
#     # Например:
#     # current_choice_quiz_words[123] = question_word
#     #
#     # Позже обработчик ответа достанет это слово
#     # и сравнит его с выбранным пользователем вариантом.
#     current_choice_quiz_words[user_id] = question_word

#     # Выбираем 3 неправильных слова
#     wrong_words = random.sample(
#         [item for item in WORDS if item["id"] != question_word["id"]],
#         3
#     )

#     # Объединяем правильный и неправильные ответы
#     options = [question_word, *wrong_words]
    
#     # Перемешиваем варианты,
#     # чтобы правильный ответ каждый раз
#     # находился на случайной позиции.
#     random.shuffle(options)

#     # Создаём кнопки с вариантами    
#     keyboard = InlineKeyboardMarkup(
#         inline_keyboard = [
#             [InlineKeyboardButton(text = options[0]['russian'], callback_data = f"choice:{options[0]['id']}")],
#             [InlineKeyboardButton(text = options[1]['russian'], callback_data = f"choice:{options[1]['id']}")],
#             [InlineKeyboardButton(text = options[2]['russian'], callback_data = f"choice:{options[2]['id']}")],
#             [InlineKeyboardButton(text = options[3]['russian'], callback_data = f"choice:{options[3]['id']}")],
#             [InlineKeyboardButton(text = "🛑 Завершить тренировку", callback_data = "finish_quiz")]
#         ]
#     )

#     # Отправляем вопрос и кнопки
#     question_message = await message.answer(
#         f"📝 Как переводится слово: {question_word['english']}?",
#         reply_markup = keyboard
#     )

#     active_quiz_message[user_id] = question_message


# @dp.callback_query(F.data == "quiz_choice")
# async def start_choice_quiz(callback: CallbackQuery) -> None:

#     # Сразу убираем загрузку у нажатой inline-кнопки.
#     await safe_callback_answer(callback)

#     # Получаем ID пользователя
#     user_id = callback.from_user.id

#     # Вызываем функцию, чтобы любая новая команда отменяла предыдущую тренировку и убирала её кнопку    
#     await cancel_active_quiz(user_id)
    
#     # Создаём статистику новой тренировки.
#     active_quiz_stats[user_id] = {
#         "correct": 0,
#         "total": 0,
#         "type": "choice"
#     }

#     logger.info(
#         "Choice quiz started | user_id=%s",
#         user_id
#     )

    
#     # Отправляем первый вопрос тренировки.
#     await send_choice_quiz(callback.message, user_id)



# @dp.callback_query(F.data == "finish_quiz")
# async def finish_quiz(callback: CallbackQuery) -> None:

#     # Сразу убираем загрузку у нажатой inline-кнопки.
#     await safe_callback_answer(callback)

#     user_id = callback.from_user.id

#     # Удаляем статистику текущей тренировки.
#     stats = active_quiz_stats.pop(user_id, None)

#     # Проверяем, существует ли ещё текущая тренировка.    
#     if not stats:
#         return

#     # Получаем тип текущей тренировки.
#     quiz_type = stats["type"] 

#     # Получаем общее количество отвеченных вопросов.
#     total_questions = stats["total"]
    
#     # Получаем количество правильных ответов.
#     correct_answers = stats["correct"]

#     # Количество ошибок
#     wrong_answers = total_questions - correct_answers

#     # Вычисляем процент правильных ответов.
#     accuracy_percent = (
#         round(correct_answers / total_questions * 100)
#         if(total_questions)
#         else 0 
#     )

#     logger.info(
#         "Quiz finished | user_id=%s | type=%s | total=%s | correct=%s | accuracy=%s%%",
#         user_id,
#         quiz_type,
#         total_questions,
#         correct_answers,
#         accuracy_percent,
#     )

#     # Удаляем активный вопрос в зависимости от типа тренировки.
#     # потому что тренировка завершена.
#     if quiz_type == "choice":
#         current_choice_quiz_words.pop(user_id, None)

#     elif quiz_type == "text":
#         current_quiz_words.pop(user_id, None)

#     # Убираем кнопку «Завершить тренировку».
#     await hide_active_quiz_keyboard(user_id)

#     # Показываем итоговый результат пользователю.
#     await callback.message.answer(
#         f"🏁 Тренировка завершена!\n\n"
#         f"Вопросов: {total_questions}\n"
#         f"Правильных: {correct_answers}\n"
#         f"Ошибок: {wrong_answers}\n"
#         f"Результат: {accuracy_percent}%\n"
#     ) 
    

# # =========================
# # ПРОВЕРКА ОТВЕТА НА ТЕСТ ПО ВЫБОРУ
# # =========================


# @dp.callback_query(F.data.startswith("choice:"))
# async def handle_quiz_test(callback: CallbackQuery) -> None:

#     # Сразу убираем загрузку у нажатой inline-кнопки.
#     await safe_callback_answer(callback)

#     user_id = callback.from_user.id

#     # Получаем ID выбранного пользователем слова
#     word_id = int(callback.data.split(":",1)[1])

#     # Проверяем, есть ли активный вопрос
#     if user_id not in current_choice_quiz_words:
#         await callback.message.answer("Этот вопрос уже отвечен.")
#         return

#     # Получаем правильное слово и удаляем его из текущего теста
#     correct_word = current_choice_quiz_words.pop(user_id)

#     # Ответ выбран - убираем кнопки со старого вопроса.
#     await hide_active_quiz_keyboard(user_id)
    
#     # Пока выбранное слово не найдено
#     selected_word = None

#     # Ищем выбранное слово по его ID
#     for item in WORDS:
#         if(item["id"] == word_id):
#             selected_word = item
#             break

#     # Проверяем, совпадает ли выбранное слово с правильным
#     is_correct = selected_word["id"] == correct_word["id"]
    
#     active_quiz_stats[user_id]["total"] += 1

#     # Обновляем статистику пользователя
#     update_stats_in_db(user_id, is_correct)

#     logger.info(
#         "Choice quiz answered | user_id=%s | correct=%s",
#         user_id,
#         is_correct,
#     )


#     # Показываем результат
#     if is_correct:
#         active_quiz_stats[user_id]["correct"] += 1
#         await callback.message.answer("✅ Правильно!")
#     else:
#         await callback.message.answer(
#             f"❌ Неправильно.\n\n"
#             f"Правильный ответ: {correct_word['russian']}"
#         )

#     if (active_quiz_stats[user_id]["type"] == "choice"):
#         await send_choice_quiz(callback.message, user_id)
#     elif (active_quiz_stats[user_id]["type"] == "favourite_choice"):
#         await send_fav_choice_quiz(callback.message, user_id)

# # =========================
# # СТАТИСТИКА
# # =========================


# @dp.message(Command("stats"))
# @dp.message(F.text == "📊 Моя статистика")
# async def show_stats(message: Message) -> None:

#     # Вызываем функцию, чтобы любая новая команда отменяла предыдущую тренировку и убирала её кнопку    
#     await cancel_active_quiz(message.from_user.id)
    
#     # Получаем ID пользователя,
#     # чтобы загрузить именно его статистику.
#     user_id = message.from_user.id

#     # Получаем из БД количество правильных ответов
#     # и общее количество попыток.
#     stats = get_stats_from_db(user_id)

#     # Если записи статистики ещё нет,
#     # пользователь пока не проходил тесты.
#     if stats is None:
#         await message.answer(
#             "📊 У тебя пока нет результатов.\n\n" "Пройди первый тест через /quiz."
#         )
#         return

#     # Распаковываем результат SELECT.
#     #
#     # Например:
#     # stats = (8, 10)
#     #
#     # Тогда:
#     # correct = 8
#     # total = 10
#     correct, total = stats

#     # Если попыток нет или статистика была сброшена,
#     # не пытаемся делить на ноль.
#     if total == 0:
#         await message.answer(
#             "📊 У тебя пока нет результатов.\n\n" "Пройди первый тест через /quiz."
#         )
#         return

#     # Вычисляем процент правильных ответов.
#     accuracy = round(correct / total * 100)

#     logger.info("Stats requested | user_id=%s", user_id)

#     # Показываем статистику пользователю.
#     await message.answer(
#         "📊 Твоя статистика\n\n"
#         f"✅ Правильных ответов: {correct}\n"
#         f"📝 Всего попыток: {total}\n"
#         f"🎯 Точность: {accuracy}% \n\n"
#         "🔄 Чтобы сбросить статистику, используй команду /reset_stats"
#     )


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
