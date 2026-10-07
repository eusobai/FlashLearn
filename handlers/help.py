
# Основные классы aiogram.
from aiogram import Router, F

# Фильтры Telegram-команд.
from aiogram.filters import Command

# Типы Telegram-объектов.
from aiogram.types import Message

# MODULES

# Функция для управления активной тренировкой.
from utils.quiz_utils import cancel_active_quiz

# =========================
# ROUTER
# =========================
router = Router()


@router.message(Command('help'))
@router.message(F.text == '❓ Помощь')
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
