# =========================
# ИМПОРТЫ
# =========================

# Основные классы aiogram.
from aiogram import Router, F

# Типы Telegram-объектов.
from aiogram.types import CallbackQuery

# Функции для работы с базой данных.
from database.database import get_words, add_fav_word_to_db

# Функция для отмены активной тренировки пользователя.
from utils.safe_calback import safe_callback_answer

# Логгер проекта для записи информации и ошибок.
from utils.logger import logger


router = Router()

WORDS = get_words() 

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

