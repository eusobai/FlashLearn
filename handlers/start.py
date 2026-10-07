# =========================
# ИМПОРТЫ
# =========================

# Основные классы aiogram.
from aiogram import Router

# Фильтры Telegram-команд.
from aiogram.filters import CommandStart

# Типы Telegram-объектов.
from aiogram.types import Message

# Функция для отмены активной тренировки пользователя.
from handlers.quiz import cancel_active_quiz

# Логгер проекта для записи информации и ошибок.
from utils.logger import logger

# Функции для работы с базой данных.
from database.database import add_user_to_db

# Главная клавиатура
from keyboards.main_keyboard import main_keyboard

router = Router()


@router.message(CommandStart())
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
