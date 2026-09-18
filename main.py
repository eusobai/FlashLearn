# =========================
# ИМПОРТЫ
# =========================

import os
import asyncio
import random
import logging
from pathlib import Path
import json

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
    Message, 
    BotCommand, 
    KeyboardButton,
    ReplyKeyboardMarkup, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup,
    CallbackQuery
)   

# Функции для работы с базой данных.
from database import (
    add_user_to_db,
    get_stats_from_db, 
    update_stats_in_db, 
    reset_stats_in_db,
    add_fav_word_to_db,
    get_fav_words_in_db,
)

# Загружает переменные из .env.
from dotenv import load_dotenv

# =========================
# НАСТРОЙКА ОКРУЖЕНИЯ
# =========================

# Загружаем данные из файла .env.
# В нашем случае оттуда берётся BOT_TOKEN.
load_dotenv()


# Получаем путь к папке, где находится main.py.
BASE_DIR = Path(__file__).resolve().parent

# Создаём папку для логов.
LOG_DIR = BASE_DIR / 'logs'
LOG_DIR.mkdir(exist_ok=True)

# =========================
# НАСТРОЙКА ЛОГИРОВАНИЯ
# =========================
logging.basicConfig(
    level= logging.INFO,
    format= '%(asctime)s | %(levelname)s %(name)s %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / 'bot.log', encoding = 'utf-8'),
        logging.StreamHandler()
    ]
)


# Создаём logger для записи событий работы бота.
logger = logging.getLogger(__name__)


# =========================
# НАСТРОЙКА BOT TOKEN
# =========================


# Получаем токен бота из .env.
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise RuntimeError('Не найден BOT_TOKEN. Добавь его в файл .env')


# Создаём объект бота и диспетчер.
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# =========================
# ЗАГРУЗКА СЛОВАРЯ
# =========================


# Открываем JSON-файл со словами.
# json.load() превращает JSON в обычный Python-список
# словарей, с которым потом работает бот.
with open('words.json', 'r', encoding = 'utf-8') as file:
    WORDS = json.load(file)



# Здесь временно хранится слово,
# на которое пользователь должен ответить в тесте.
#
# Формат примерно такой:
#
# {
#     user_id: {
#         "english": "factory",
#         "russian": "завод"
#     }
# }
current_quiz_words = {}


# =========================
# ГЛАВНАЯ КЛАВИАТУРА
# =========================

# Это обычная клавиатура Telegram.
# Её кнопки отправляют боту обычный текст.
main_keyboard = ReplyKeyboardMarkup(
    keyboard=
        [ 
        [KeyboardButton(text='📚 Получить карточку')],
        [KeyboardButton(text = '📝 Пройти тест')],
        [KeyboardButton(text = '📊 Моя статистика')],
        [KeyboardButton(text='⭐ Избранные слова')]
        ],
    resize_keyboard = True,
    input_field_placeholder = 'Выбери действие',

)


# =========================
# /START
# =========================


@dp.message(CommandStart())
async def cmd_start(message: Message) -> None:
    # Получаем имя пользователя.
    # Если username отсутствует, используем "unknown".
    username = message.from_user.username if message.from_user.username else 'unknown'

    # Telegram ID нужен для связи пользователя
    # с его статистикой и избранными словами в БД.
    user_id = message.from_user.id

    # Добавляем пользователя в БД.
    # Если пользователь уже существует, функция
    # не создаёт дубликат.
    add_user_to_db(user_id)


    logger.info(
        'The user is connected | username=%s | user_id=%s', username, user_id
    )


    # Отправляем приветствие и показываем главную клавиатуру.
    await message.answer(
        "Привет! Я помогу тебе учить английский.\n\n"
        "Выбери действие на клавиатуре ниже.",
        reply_markup= main_keyboard, 
    )


# =========================
# КАРТОЧКА
# =========================


@dp.message(Command('card'))
@dp.message(F.text == '📚 Получить карточку')
async def send_card(message: Message) -> None:
    # Выбираем случайное слово из словаря.
    word = random.choice(WORDS)

    username = message.from_user.username if message.from_user.username else 'unknown'


    logger.info(
        'Card sent | username=%s | word=%s',
        username,
        word["english"]
    )


    # Создаём inline-кнопку.
    #
    # text — текст, который видит пользователь.
    #
    # callback_data — данные, которые получит бот
    # после нажатия кнопки.
    #
    # Например:
    # favourite:factory
    #
    # Благодаря этому бот знает,
    # какое слово нужно добавить в избранное.
    favourite_button = InlineKeyboardButton(
        text = '⭐ Добавить в избранное',
        callback_data = f'favourite:{word['english']}'
    )


    # Создаём inline-клавиатуру и помещаем кнопку в неё.
    favorite_keybord = InlineKeyboardMarkup(
        inline_keyboard=[
            [favourite_button]
        ]
    )


    # Отправляем карточку и прикрепляем inline-кнопку.
    await message.answer(
        f'📚 Карточка\n\n'
        f'Английское слово: {word['english']}\n'
        f'Перевод: {word['russian']}',
        reply_markup= favorite_keybord
    )


# =========================
# ДОБАВЛЕНИЕ В ИЗБРАННОЕ
# =========================

# Обработчик срабатывает, когда пользователь нажимает
# inline-кнопку, у которой callback_data начинается с "favourite:".
@dp.callback_query(F.data.startswith('favourite:'))
async def handle_add_favourite(callback: CallbackQuery) -> None:
    # Получаем Telegram ID пользователя,
    # который нажал кнопку.
    user_id = callback.from_user.id


    # Получаем callback_data.
    #
    # Например:
    # "favourite:factory"
    #
    # split(":", 1) разделяет строку только один раз:
    #
    # ["favourite", "factory"]
    #
    # [1] берёт второй элемент — "factory".
    english_word = callback.data.split(':', 1)[1]

    # Пока слово не найдено.
    word = None

    # Ищем полную запись слова в WORDS.
    # Нам нужен не только английский вариант,
    # но и русский перевод.
    for item in WORDS:
        if item['english'] == english_word:
            word = item
            break


    # Если слово не найдено в JSON,
    # прекращаем выполнение обработчика.
    if word is None:
        await callback.answer("❌ Слово не найдено.")
        return


    # Сохраняем в БД:
    # ID пользователя,
    # английское слово,
    # перевод.
    add_fav_word_to_db(
        user_id, 
        word['english'], 
        word['russian']
    )

    logger.info(
        'The favourite word has been added | user_id=%s | word=%s | translation=%s',
        user_id, 
        word['english'], 
        word['russian']
    )


    # Показываем пользователю небольшое уведомление
    # после успешного добавления.
    await callback.answer("⭐ Добавлено в избранное!")


@dp.message(F.text == '⭐ Избранные слова')
@dp.message(Command('favourites'))
async def get_fav_word(message: Message) -> None:
    # Получаем ID пользователя.
    user_id = message.from_user.id

    # Получаем все избранные слова этого польщователя из бд.
    fav_words = get_fav_words_in_db(user_id)

    # Если избранных слов нет, сообщаем об этом пользователю.  
    if not fav_words:
        await message.answer(
            'У тебя пока нет избранных слов.')
        return
    
    # Создаем список слов для красивого сообщения
    lines = []

    for word,translation in fav_words:
        lines.append( f'{word} - {translation}')

    text = '⭐ Твои избранные слова: \n\n' + '\n'.join(lines)

    await message.answer(text)
# =========================
# НАЧАЛО ТЕСТА
# =========================


@dp.message(Command('quiz'))
@dp.message(F.text =='📝 Пройти тест')
async def start_quiz(message: Message) -> None:
    # Получаем ID пользователя.
    user_id = message.from_user.id

    # Выбираем случайное слово.
    word = random.choice(WORDS)

    # Сохраняем текущее слово для пользователя.
    #
    # Это нужно, чтобы после ответа пользователя
    # бот понял, какое слово он должен проверить.
    current_quiz_words[user_id] = word


    logger.info(
        'Quiz started | user_id=%s | word=%s',
        user_id, word['english']
    )

    # Отправляем пользователю вопрос.
    await message.answer(
        f'📝 Как переводиться слово: {word['english']}?'
    )


# =========================
# СТАТИСТИКА
# =========================
@dp.message(Command('stats'))
@dp.message(F.text == '📊 Моя статистика')
async def show_stats(message: Message) -> None:
    # Получаем ID пользователя,
    # чтобы загрузить именно его статистику.
    user_id =  message.from_user.id

    # Получаем из БД количество правильных ответов
    # и общее количество попыток.
    stats = get_stats_from_db(user_id)

    # Если записи статистики ещё нет,
    # пользователь пока не проходил тесты.
    if stats is None:
        await message.answer(
            '📊 У тебя пока нет результатов.\n\n'
            'Пройди первый тест через /quiz.'
        )
        return


    # Распаковываем результат SELECT.
    #
    # Например:
    # stats = (8, 10)
    #
    # Тогда:
    # correct = 8
    # total = 10ы
    correct, total = stats

    # Если попыток нет или статистика была сброшена,
    # не пытаемся делить на ноль.
    if total == 0:
        await message.answer(
            '📊 У тебя пока нет результатов.\n\n'
            'Пройди первый тест через /quiz.'

        )   
        return


    # Вычисляем процент правильных ответов.
    accuracy = round(correct / total * 100)


    logger.info('Stats requested | user_id=%s', user_id)

    # Показываем статистику пользователю.
    await message.answer(
        "📊 Твоя статистика\n\n"
        f"✅ Правильных ответов: {correct}\n"
        f"📝 Всего попыток: {total}\n"
        f"🎯 Точность: {accuracy}% \n\n"
        '🔄 Чтобы сбросить статистику, используй команду /reset_stats'
    )


# =========================
# СБРОС СТАТИСТИКИ
# =========================


@dp.message(Command('reset_stats'))
async def reset_user_stats(message: Message) -> None:
    # Определяем, статистику какого пользователя нужно сбросить.
    user_id = message.from_user.id

    # Передаём ID пользователя в функцию БД.
    reset_stats_in_db(user_id)


    logger.info(
        'The user statistics have been reset. | user_id=%s',
        user_id
    )


    await message.answer('Твоя статистика успешно сброшена!')


# =========================
# ПРОВЕРКА ОТВЕТА НА ТЕСТ
# =========================


@dp.message(F.text)
async def handle_text(message: Message) -> None:
    user_id = message.from_user.id

    # Получаем текст ответа пользователя.
    # strip() убирает пробелы по краям.
    text = message.text.strip()

    # Проверяем, есть ли у пользователя активный вопрос.
    if user_id in current_quiz_words:

        # Получаем слово, которое пользователь должен был перевести,
        # и сразу удаляем его из текущего теста.
        word = current_quiz_words.pop(user_id)

        # В JSON может быть несколько переводов:
        #
        # "завод, фабрика"
        #
        # split(",") разделяет их на отдельные варианты.
        #
        # strip() убирает пробелы.
        # lower() приводит всё к нижнему регистру.
        correct_answers = [
            answer.strip().lower()
            for answer in word['russian'].split(',')
        ]

        # Проверяем, находится ли ответ пользователя
        # среди допустимых переводов.
        is_correct = text.lower() in correct_answers

        # Обновляем статистику пользователя в БД.
        update_stats_in_db(user_id, is_correct) 


        logger.info(
            "Quiz answered | user_id=%s | correct=%s",
            user_id,
            is_correct,
        )

        # Если пользователь ответил правильно.
        if is_correct:
            # Находим все правильные варианты,
            # кроме того, который уже написал пользователь.
            other_answers = [
                answer
                for answer in correct_answers
                if answer != text
            ]
      
            
            # Если есть другие допустимые переводы,
            # показываем их пользователю.
            if other_answers:
                await message.answer(
                    "✅ Правильно!\n\n" 
                    f"Другие варианты: {', '.join(other_answers)}"
                )
            else:
                await message.answer('✅ Правильно! Молодец.')

        # Если ответ неправильный.
        else:
            await message.answer(
                "❌ Неправильно.\n\n" 
                f"Правильные ответы: {', '.join(correct_answers)}"
                )
            
        # Останавливаем обработчик,
        # чтобы сообщение не пошло дальше.
        return
    
    # Если пользователь не отвечает на активный тест,
    # бот сообщает, что не знает, что делать с сообщением.
    await message.answer('Не понял сообщение. Выбери действие на клавиатуре или используй /start.')



# =========================
# ЗАПУСК БОТА
# =========================


async def main() -> None:

    # Регистрируем команды, которые Telegram
    # будет показывать пользователю.
    await bot.set_my_commands(
        [
            BotCommand(command='start', description='Запустить бота'),
            BotCommand(command='card', description='Получить случайную карту'),
            BotCommand(command='quiz',description='Проверить перевод слова'),
            BotCommand(command='stats', description='Посмотреть статистику'),
            BotCommand(command='favourites', description='Посмотреть избранные слова'),
        ]
    )

    logger.info('Bot запустился')

    # Запускаем бота и начинаем получать сообщения
    # от Telegram.
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())