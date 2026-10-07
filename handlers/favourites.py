# =========================
# ИМПОРТЫ
# =========================

# Основные классы aiogram.
from aiogram import Router, F

# Типы Telegram-объектов.
from aiogram.types import (
    CallbackQuery, 
    Message, 
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
# Фильтры Telegram-команд.
from aiogram.filters import Command

# Функции для работы с базой данных.
from database.database import (
    get_words, 
    add_fav_word_to_db, 
    get_fav_words_in_db,
    delete_fav_word_in_db
)

# Функция для отмены активной тренировки пользователя.
from handlers.quiz import cancel_active_quiz

# Безопасно подтверждает нажатие inline-кнопки.
# Это нужно делать сразу, чтобы у пользователя не крутилась загрузка.
from utils.safe_calback import safe_callback_answer

# Логгер проекта для записи информации и ошибок.
from utils.logger import logger


router = Router()

WORDS = get_words() 


# # =========================
# # ДОБАВЛЕНИЕ В ИЗБРАННОЕ
# # =========================


# Обработчик срабатывает, когда пользователь нажимает
# inline-кнопку, у которой callback_data начинается с "favourite:".
@router.callback_query(F.data.startswith("favourite:"))
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


@router.message(F.text == "⭐ Мои слова")
@router.message(Command("favourites"))
async def get_fav_word(message: Message) -> None:

    # Вызываем функцию, чтобы любая новая команда отменяла предыдущую тренировку и убирала её кнопку    
    await cancel_active_quiz(message.from_user.id)

    # Получаем ID пользователя.
    user_id = message.from_user.id

    # Получаем все избранные слова этого пользователя из БД.
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

@router.callback_query(F.data.startswith("remove_fav_word:"))
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


# # =========================
# # НАЧАЛО ТРЕНИРОВКИ ИЗБРАННЫХ СЛОВ
# # =========================

@router.callback_query(F.data == "quiz_favourites")
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
