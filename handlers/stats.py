# =========================
# ИМПОРТЫ
# =========================

# # Основные классы aiogram.
from aiogram import Router, F

# Фильтры Telegram-команд.
from aiogram.filters import Command

# Типы Telegram-объектов.
from aiogram.types import Message

# Функция для отмены активной тренировки пользователя.
from utils.quiz_utils import cancel_active_quiz

# Функции для работы с базой данных.
from database.database import get_stats_from_db, reset_stats_in_db

# Логгер проекта для записи информации и ошибок.
from utils.logger import logger


# =========================
# РОУТЕР
# =========================
router = Router()


# =========================
# ПРОВЕРКА СТАТИСТИКИ
# =========================


@router.message(Command("stats"))
@router.message(F.text == "📊 Моя статистика")
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


@router.message(Command("reset_stats"))
async def reset_user_stats(message: Message) -> None:

    # Вызываем функцию, чтобы любая новая команда отменяла предыдущую тренировку и убирала её кнопку    
    await cancel_active_quiz(message.from_user.id)
    
    # Определяем, статистику какого пользователя нужно сбросить.
    user_id = message.from_user.id

    # Передаём ID пользователя в функцию БД.
    reset_stats_in_db(user_id)

    logger.info("The user statistics have been reset. | user_id=%s", user_id)

    await message.answer("Твоя статистика успешно сброшена!")

