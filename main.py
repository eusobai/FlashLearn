# =========================
# ИМПОРТЫ
# =========================

import os
import asyncio

# from MODULES
from utils.logger import logger

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
from aiogram import Bot, Dispatcher


# Типы Telegram-объектов:
# BotCommand — команда бота,
from aiogram.types import (
    BotCommand,
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
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("Не найден BOT_TOKEN. Добавь его в файл .env")


# Создаём объект бота и диспетчер.
bot = Bot(token = BOT_TOKEN)
dp = Dispatcher()


# =========================
# ПОДКЛЮЧЕНИЕ РОУТЕРОВ
# =========================

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
