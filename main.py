# =========================
# ИМПОРТЫ
# =========================

import os
import asyncio
import random
import logging
from pathlib import Path

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
    CallbackQuery,
)

# Обрабатывает ошибку Telegram, когда пользователь нажал старую кнопку
# и Telegram уже не принимает ответ на это нажатие.
from aiogram.exceptions import TelegramBadRequest

# Функции для работы с базой данных.
from database import (
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


# Получаем путь к папке, где находится main.py.
BASE_DIR = Path(__file__).resolve().parent

# Создаём папку для логов.
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

# =========================
# НАСТРОЙКА ЛОГИРОВАНИЯ
# =========================
logging.basicConfig(
    level = logging.INFO,
    format = "%(asctime)s | %(levelname)s %(name)s %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "bot.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)

logging.getLogger('aiogram').setLevel(logging.WARNING)

# Создаём logger для записи событий работы бота.
logger = logging.getLogger(__name__)


# Безопасно подтверждает нажатие inline-кнопки.
# Это нужно делать сразу, чтобы у пользователя не крутилась загрузка.
async def safe_callback_answer(callback: CallbackQuery, text: str = "") -> None:
    try:
        await callback.answer(text = text)  # сразу останавливает загрузку кнопки
    except TelegramBadRequest as error:
        # Такая ошибка возникает, если нажатие слишком старое:
        # например, сервер временно не мог связаться с Telegram.
        if "query is too old" in str(error):
            logger.warning(
                "Старое нажатие кнопки пропущено | user_id=%s",
                callback.from_user.id,
            )
        else:
            # Другие ошибки не скрываем — их нужно видеть в логах.
            raise

# =========================
# НАСТРОЙКА BOT TOKEN
# =========================


# Получаем токен бота из .env.
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("Не найден BOT_TOKEN. Добавь его в файл .env")


# Создаём объект бота и диспетчер.
bot = Bot(token = BOT_TOKEN)
dp = Dispatcher()


# =========================
# ЗАГРУЗКА СЛОВАРЯ
# =========================
WORDS = get_words()


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
    



# =========================
# ГЛАВНАЯ КЛАВИАТУРА
# =========================

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


# =========================
# /START
# =========================


@dp.message(CommandStart())
async def cmd_start(message: Message) -> None:

    # Вызываем функцию, чтобы любая новая команда отменяла предыдущую тренировку и убирала её кнопку    
    await cancel_active_quiz(message.from_user.id)

    # Получаем имя пользователя.
    # Если username отсутствует, используем "unknown".
    username = message.from_user.username if message.from_user.username else "unknown"
    user_fullname= message.from_user.full_name if message.from_user.full_name else "unknown"

    # Telegram ID нужен для связи пользователя
    # с его статистикой и избранными словами в БД.
    user_id = message.from_user.id

    # Добавляем пользователя в БД.
    # Если пользователь уже существует, функция
    # не создаёт дубликат.
    add_user_to_db(user_id)

    logger.info("The user is connected | username=%s | user_id=%s | fullname=%s" , username, user_id, user_fullname)

    # Отправляем приветствие и показываем главную клавиатуру.
    await message.answer(
        "Привет! Я помогу тебе учить английский.\n\n"
        "Выбери действие на клавиатуре ниже.",
        reply_markup=main_keyboard,
    )


# =========================
# /HELP
# =========================


@dp.message(Command('help'))
@dp.message(F.text == '❓ Помощь')
async def cmd_help(message:Message) -> None:
    
    # Вызываем функцию, чтобы любая новая команда отменяла предыдущую тренировку и убирала её кнопку    
    await cancel_active_quiz(message.from_user.id)
    
    await message.answer(
        "📚 Что я умею:\n\n"
        "📚 Учить слова - получить случайное английское слово.\n"
        "🧠 Тренировка - проверить свои знания.\n"
        "📊 Моя статистика - посмотреть результат тестов.\n"
        "⭐ Мои слова - посмотреть сохранённые слова.\n\n"
        "/start - открыть главное меню.\n"
        "/help - показать эту справку."
    )



# =========================
# КАРТОЧКА
# =========================


@dp.message(Command("card"))
@dp.message(F.text == "📚 Учить слова")
async def send_card(message: Message) -> None:

    # Вызываем функцию, чтобы любая новая команда отменяла предыдущую тренировку и убирала её кнопку    
    await cancel_active_quiz(message.from_user.id)
    
    # Выбираем случайное слово из словаря.
    word = random.choice(WORDS)

    username = message.from_user.username if message.from_user.username else "unknown"

    logger.info("Card sent | username=%s | word=%s", username, word["english"])

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
        text = "⭐ Добавить в мои слова", callback_data=f"favourite:{word['id']}"
    )

    # Создаём inline-клавиатуру и помещаем кнопку в неё.
    favorite_keyboard = InlineKeyboardMarkup(inline_keyboard=[[favourite_button]])

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


# =========================
# ДОБАВЛЕНИЕ В ИЗБРАННОЕ
# =========================



# Обработчик срабатывает, когда пользователь нажимает
# inline-кнопку, у которой callback_data начинается с "favourite:".
@dp.callback_query(F.data.startswith("favourite:"))
async def handle_add_favourite(callback: CallbackQuery) -> None:

    # Сразу убираем загрузку у нажатой inline-кнопки.
    await safe_callback_answer(callback, "⏳ Добавляю слово...")

    # Получаем Telegram ID пользователя,
    # который нажал кнопку.
    user_id = callback.from_user.id

    # Получаем callback_data.
    #
    # Например:
    # "favourite:85"
    #
    # split(":", 1) разделяет строку только один раз:
    #
    # ["favourite", "85"]
    #
    # [1] берёт второй элемент — "85".
    word_id = int(callback.data.split(":", 1)[1])

    # Пока слово не найдено.
    word = None

    # Ищем полную запись слова в WORDS.
    for item in WORDS:
        if item["id"] == word_id:
            word = item
            break

    # Если слова нет в загруженном словаре WORDS.
    # прекращаем выполнение обработчика.
    if word is None:
        await callback.message.answer("❌ Слово не найдено.")
        return

    # Сохраняем в БД:
    # ID пользователя,
    # ID Слова
    add_fav_word_to_db(user_id, word["id"])

    logger.info(
        "The favourite word has been added | user_id=%s | word=%s | translation=%s",
        user_id,
        word["english"],
        word["russian"],
    )

    # Показываем пользователю небольшое уведомление
    # после успешного добавления.
    await callback.message.answer("⭐ Добавлен в мои слова!")


# =========================
# ПОЛУЧЕНИЕ ИЗБРАННЫХ СЛОВ
# =========================

def get_word_form(number: int, forms: tuple[str, str, str]) -> str:
    """
    Выбирает правильную форму слова в зависимости от числа.

    forms — три формы слова:
    1) для 1
    2) для 2-4
    3) для 5 и больше

    Например:
    ("слово", "слова", "слов")

    Результат:
    1 → слово
    2 → слова
    5 → слов
    21 → слово
    22 → слова
    25 → слов
    """

    # Берём последние две цифры числа.
    n = abs(number) % 100

    # Берём последнюю цифру числа.
    n1 = n % 10

    # Числа от 11 до 14 всегда используют форму "слов".
    if 10 < n < 20:
        return forms[2]

    # Числа, заканчивающиеся на 1:
    # 1, 21, 31, 101 и т.д.
    if n1 == 1:
        return forms[0]

    # Числа, заканчивающиеся на 2, 3 или 4:
    # 2, 3, 4, 22, 23, 24 и т.д.
    if 1 < n1 < 5:
        return forms[1]

    # Все остальные числа:
    # 5, 6, 10, 15, 20, 25 и т.д.
    return forms[2]


@dp.message(F.text == "⭐ Мои слова")
@dp.message(Command("favourites"))
async def get_fav_word(message: Message) -> None:

    # Вызываем функцию, чтобы любая новая команда отменяла предыдущую тренировку и убирала её кнопку    
    await cancel_active_quiz(message.from_user.id)

    # Получаем ID пользователя.
    user_id = message.from_user.id

    # Получ
    # 
    # аем все избранные слова этого пользователя из БД.
    fav_words = get_fav_words_in_db(user_id)

    # Если избранных слов нет, сообщаем об этом пользователю.
    if not fav_words:
        await message.answer(
            "📖 У тебя пока нет сохранённых слов."
        )
        return

    # Создаём список строк для красивого сообщения.
    lines = []

    # Создаем список inline-кнопок
    remove_buttons = []

    # Проходим по каждому сохранённому слову.
    for item in fav_words:

        # Добавляем информацию о слове в текст.
        lines.append(
            f"📚 Слово: <b>{item['english']}</b>\n"
            f"RU Перевод: {item['russian']}\n"
            f"📖 Определение: {item['definition']}\n"
            f"💬 Пример: {item['example']}\n"
            f"🔊 Произношение: {item['pronunciation']}"
        )

        # Создаём кнопку удаления именно для этого слова.
        remove_buttons.append(
            [
                InlineKeyboardButton(
                    text = f"🗑 Удалить {item['english']}",
                    callback_data = f"remove_fav_word:{item['id']}"
                )
            ]
        )

    # Получаем количество сохранённых слов.
    count = len(fav_words)

    # Получаем правильную форму слова:
    # "1 слово", "2 слова", "5 слов", "21 слово" и т.д.
    word_form = get_word_form(
        count,
        ("слово", "слова", "слов")
    )

    # Создаём итоговый текст сообщения.
    text = (
        "⭐ Твои сохранённые слова:\n\n"
        + f"У тебя сохранено: {count} {word_form}\n\n"
        + "\n\n".join(lines)
    )

    # Создаём inline-кнопку.
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            *remove_buttons,
            [
                InlineKeyboardButton(
                    text="🧠 Тренировка моих слов",
                    callback_data="quiz_favourites"
                )
            ]
        ]
    )

    # Записываем в лог информацию о том,
    # что список избранных слов был отправлен.
    logger.info(
        "Favourites words were sent | user_id=%s",
        user_id
    )

    # Отправляем пользователю список слов и кнопку.
    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=keyboard
    )

# =========================
# УДАЛЕНИЕ ИЗБРАННОГО СЛОВО
# =========================

@dp.callback_query(F.data.startswith("remove_fav_word:"))
async def delete_fav_word(callback: CallbackQuery):

    # Сразу убираем загрузку у нажатой inline-кнопки.
    await safe_callback_answer(callback, "⏳ Удаляю слово...")

    user_id = callback.from_user.id

    word_id = int(callback.data.split(":", 1)[1])

    delete_fav_word_in_db(user_id, word_id)

    logger.info(
        "Favourites word has been removed | user_id=%s | word_id=%s",
        user_id, word_id
    )

    await callback.message.answer("🗑 Слово удалено!")


# =========================
# НАЧАЛО ТРЕНИРОВКИ ИЗБРАННЫХ СЛОВ
# =========================

@dp.callback_query(F.data == "quiz_favourites")
async def start_fav_quiz(callback: CallbackQuery) -> None:

    # Сразу убираем загрузку у нажатой inline-кнопки.
    await safe_callback_answer(callback)

    # Получаем ID пользователя, который нажал кнопку.
    user_id = callback.from_user.id
    
    # Получаем все сохранённые слова этого пользователя из базы данных.
    favourite_words = get_fav_words_in_db(user_id)

    # Если сохранённых слов нет, сообщаем об этом пользователю.
    if not favourite_words:
        await callback.message.answer(
            "⭐ У тебя пока нет сохранённых слов."
        )
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard = [
            [
                InlineKeyboardButton(text = "🎯 Выбор ответа", callback_data = "favourite_quiz_choice")
            ],
            [
                InlineKeyboardButton(text = "✍️ Написать ответ", callback_data = "favourite_quiz_text")
            ]
        ]
    )

    # Отправляем пользователю вопрос для тренировки.
    await callback.message.answer(
        "🧠 Выбери режим тренировки:",
        reply_markup = keyboard
    )




# =========================
# СТАРТ ТЕКСТОВОГО ТЕСТА ИЗБРАННЫХ СЛОВ
# =========================

@dp.callback_query(F.data == "favourite_quiz_text")
async def start_fav_text_quiz(callback: CallbackQuery) -> None:

    # Сразу отвечаем на callback, чтобы Telegram убрал индикатор загрузки
    # после нажатия пользователем на кнопку.    
    await safe_callback_answer(callback)

    user_id = callback.from_user.id

    # Получаем все избранные слова пользователя
    # и случайно выбираем первое слово для тренировки.
    question_favourite_word = random.choice(get_fav_words_in_db(user_id))
    
    # Если у пользователя уже была другая активная тренировка,
    # завершаем её перед запуском новой.
    await cancel_active_quiz(user_id)

    # Создаём статистику новой тренировки.
    active_quiz_stats[user_id] = {
        "correct": 0,
        "total": 0,
        "type": "favourite_text"
    }

    logger.info(
        "Favourite text quiz started | user_id=%s",
        user_id
    )
    
    # Сохраняем выбранное слово как текущее слово пользователя.
    # Именно его перевод пользователь должен написать сейчас.
    current_quiz_words[user_id] = question_favourite_word

    # Создаём кнопку для досрочного завершения тренировки.
    keyboard = InlineKeyboardMarkup(
        inline_keyboard = [
            [InlineKeyboardButton( text="🛑 Завершить тренировку", callback_data="finish_quiz")]
        ]
    )

    # Отправляем пользователю первый вопрос тренировки.
    question_message = await callback.message.answer(
        f"📝 Как переводится слово: {question_favourite_word['english']}?\n\n",
        reply_markup = keyboard
    )

    # Сохраняем сообщение с текущим вопросом,
    # чтобы позже можно было работать именно с ним.
    active_quiz_message[user_id] = question_message


# =========================
# СТАРТ ТЕСТА С ВЫБОРАМИ ИЗ ИЗБРАННЫХ СЛОВ
# =========================

async def send_fav_choice_quiz(message: Message, user_id: int):

    favourite_words = get_fav_words_in_db(user_id)

    # Для теста с вариантами нужно минимум 2 слова.
    if (len(favourite_words) < 2):
        await message.answer("⭐ Для тренировки с вариантами нужно минимум 2 избранных слова.")
        return

    question_word = random.choice(get_fav_words_in_db(user_id))

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
                InlineKeyboardButton(text = option["russian"], callback_data = f"choice:{option["id"]}")
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



@dp.callback_query(F.data == "favourite_quiz_choice")
async def start_fav_choice_quiz(callback: CallbackQuery) -> None:

    await safe_callback_answer(callback)

    user_id = callback.from_user.id

    await cancel_active_quiz(user_id)
     
    active_quiz_stats[user_id] = {
        "correct": 0,
        "total": 0,
        "type": "favourite_choice"
    }
    
    logger.info(
        "Favourite choice quiz started | user_id=%s",
        user_id
    )
    
    await send_fav_choice_quiz(callback.message, user_id)


# =========================
# НАЧАЛО ТЕСТА
# =========================


@dp.message(Command("quiz"))
@dp.message(F.text == "🧠 Тренировка")
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
# СТАРТ ТЕКСТОВОГО ТЕСТА
# =========================

# Этот обработчик срабатывает,
# когда пользователь нажимает inline-кнопку
# "✍️ Написать ответ".
@dp.callback_query(F.data == "quiz_text")
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


@dp.callback_query(F.data == "quiz_choice")
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



@dp.callback_query(F.data == "finish_quiz")
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
    

# =========================
# ПРОВЕРКА ОТВЕТА НА ТЕСТ ПО ВЫБОРУ
# =========================


@dp.callback_query(F.data.startswith("choice:"))
async def handle_quiz_test(callback: CallbackQuery) -> None:

    # Сразу убираем загрузку у нажатой inline-кнопки.
    await safe_callback_answer(callback)

    user_id = callback.from_user.id

    # Получаем ID выбранного пользователем слова
    word_id = int(callback.data.split(":",1)[1])

    # Проверяем, есть ли активный вопрос
    if user_id not in current_choice_quiz_words:
        await callback.message.answer("Этот вопрос уже отвечен.")
        return

    # Получаем правильное слово и удаляем его из текущего теста
    correct_word = current_choice_quiz_words.pop(user_id)

    # Ответ выбран - убираем кнопки со старого вопроса.
    await hide_active_quiz_keyboard(user_id)
    
    # Пока выбранное слово не найдено
    selected_word = None

    # Ищем выбранное слово по его ID
    for item in WORDS:
        if(item["id"] == word_id):
            selected_word = item
            break

    # Проверяем, совпадает ли выбранное слово с правильным
    is_correct = selected_word["id"] == correct_word["id"]
    
    active_quiz_stats[user_id]["total"] += 1

    # Обновляем статистику пользователя
    update_stats_in_db(user_id, is_correct)

    logger.info(
        "Choice quiz answered | user_id=%s | correct=%s",
        user_id,
        is_correct,
    )


    # Показываем результат
    if is_correct:
        active_quiz_stats[user_id]["correct"] += 1
        await callback.message.answer("✅ Правильно!")
    else:
        await callback.message.answer(
            f"❌ Неправильно.\n\n"
            f"Правильный ответ: {correct_word['russian']}"
        )

    if (active_quiz_stats[user_id]["type"] == "choice"):
        await send_choice_quiz(callback.message, user_id)
    elif (active_quiz_stats[user_id]["type"] == "favourite_choice"):
        await send_fav_choice_quiz(callback.message, user_id)

# =========================
# СТАТИСТИКА
# =========================


@dp.message(Command("stats"))
@dp.message(F.text == "📊 Моя статистика")
async def show_stats(message: Message) -> None:

    # Вызываем функцию, чтобы любая новая команда отменяла предыдущую тренировку и убирала её кнопку    
    await cancel_active_quiz(message.from_user.id)
    
    # Получаем ID пользователя,
    # чтобы загрузить именно его статистику.
    user_id = message.from_user.id

    # Получаем из БД количество правильных ответов
    # и общее количество попыток.
    stats = get_stats_from_db(user_id)

    # Если записи статистики ещё нет,
    # пользователь пока не проходил тесты.
    if stats is None:
        await message.answer(
            "📊 У тебя пока нет результатов.\n\n" "Пройди первый тест через /quiz."
        )
        return

    # Распаковываем результат SELECT.
    #
    # Например:
    # stats = (8, 10)
    #
    # Тогда:
    # correct = 8
    # total = 10
    correct, total = stats

    # Если попыток нет или статистика была сброшена,
    # не пытаемся делить на ноль.
    if total == 0:
        await message.answer(
            "📊 У тебя пока нет результатов.\n\n" "Пройди первый тест через /quiz."
        )
        return

    # Вычисляем процент правильных ответов.
    accuracy = round(correct / total * 100)

    logger.info("Stats requested | user_id=%s", user_id)

    # Показываем статистику пользователю.
    await message.answer(
        "📊 Твоя статистика\n\n"
        f"✅ Правильных ответов: {correct}\n"
        f"📝 Всего попыток: {total}\n"
        f"🎯 Точность: {accuracy}% \n\n"
        "🔄 Чтобы сбросить статистику, используй команду /reset_stats"
    )


# =========================
# СБРОС СТАТИСТИКИ
# =========================


@dp.message(Command("reset_stats"))
async def reset_user_stats(message: Message) -> None:

    # Вызываем функцию, чтобы любая новая команда отменяла предыдущую тренировку и убирала её кнопку    
    await cancel_active_quiz(message.from_user.id)
    
    # Определяем, статистику какого пользователя нужно сбросить.
    user_id = message.from_user.id

    # Передаём ID пользователя в функцию БД.
    reset_stats_in_db(user_id)

    logger.info("The user statistics have been reset. | user_id=%s", user_id)

    await message.answer("Твоя статистика успешно сброшена!")


# =========================
# ПРОВЕРКА ОТВЕТА НА ТЕСТ
# =========================


@dp.message(F.text)
async def handle_text_answer(message: Message) -> None:
    user_id = message.from_user.id

    # Получаем текст ответа пользователя.
    # strip() убирает пробелы по краям.
    text = message.text.strip()

    # Проверяем, есть ли у пользователя активный вопрос.
    if user_id in current_quiz_words:

        # Получаем слово, которое пользователь должен был перевести,
        # и сразу удаляем его из текущего теста.
        correct_word = current_quiz_words.pop(user_id)
        
        # Ответ получен - кнопка завершения на старом вопросе больше не нужна.
        await hide_active_quiz_keyboard(user_id)
        
        # В БД может быть несколько переводов:
        #
        # "завод, фабрика"
        #
        # split(";") разделяет их на отдельные варианты.
        #
        # strip() убирает пробелы.
        # lower() приводит всё к нижнему регистру.
        correct_answers = [
            answer.strip().lower() for answer in correct_word["russian"].split(";")
        ]

        # Проверяем, находится ли ответ пользователя
        # среди допустимых переводов.
        is_correct = text.lower() in correct_answers

        # Обновляем статистику текущей тренировки.
        active_quiz_stats[user_id]["total"] += 1
        
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
            active_quiz_stats[user_id]["correct"] += 1

            other_answers = [
                answer for answer in correct_answers 
                if answer != text.lower()
            ]

            # Если есть другие допустимые переводы,
            # показываем их пользователю.
            if other_answers:
                await message.answer(
                    "✅ Правильно!\n\n" f"Другие варианты: {', '.join(other_answers)}"
                )
            else:
                await message.answer("✅ Правильно! Молодец.")
                
        # Если ответ неправильный.
        else:
            await message.answer(
                "❌ Неправильно.\n\n" f"Правильные ответы: {', '.join(correct_answers)}"
            )

        # Сюда будем записывать следующее слово для следующего вопроса.
        next_word = None

        # Если это обычная текстовая тренировка,
        # берём следующее слово из общего списка WORDS.
        if (active_quiz_stats[user_id]["type"] == "text"):
            next_word = random.choice(WORDS)

        # Если это текстовая тренировка только из избранных слов,
        # берём следующее слово только из избранных слов пользователя.
        elif (active_quiz_stats[user_id]["type"] == "favourite_text"):
            next_word = random.choice(get_fav_words_in_db(user_id))    

        # Сохраняем выбранное слово как текущее слово для следующего ответа пользователя.
        current_quiz_words[user_id] = next_word

        keyboard = InlineKeyboardMarkup(
            inline_keyboard = [
                [InlineKeyboardButton(text="🛑 Завершить тренировку", callback_data="finish_quiz")]
            ]
        )

        question_message = await message.answer(
            f"📝 Как переводится слово: {next_word['english']}?",
            reply_markup = keyboard
        )
        active_quiz_message[user_id] = question_message
        # Останавливаем обработчик
        return

    # Если пользователь не отвечает на активный тест,
    # бот сообщает, что не знает, что делать с сообщением.
    await message.answer(
        "Не понял сообщение. Выбери действие на клавиатуре или используй /start."
    )

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
