import os
import asyncio
import random

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, BotCommand

from dotenv import load_dotenv
load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise RuntimeError('Не найден BOT_TOKEN. Добавь его в файл .env')


bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
WORDS =[
    {"english": "apple", "russian": "яблоко"},
    {"english": "book", "russian": "книга"},
    {"english": "house", "russian": "дом"},
    {"english": "water", "russian": "вода"},
    {"english": "friend", "russian": "друг"},
]

@dp.message(CommandStart())
async def cmd_start(message: Message) -> None:
    await message.answer(
        "Привет! Я помогу тебе учить английский.\n\n"
        "Доступные команды:\n"
        "/card — получить случайную карточку"
    )


@dp.message(Command('card'))
async def send_card(message: Message) -> None:
    word = random.choice(WORDS)
    await message.answer(
        f'📚 Карточка\n\n'
        f'Английское слово: {word['english']}\n'
        f'Перевод: {word['russian']}'
    )

@dp.message()
async def echo_text(message: Message) -> None:
    print(f'(log) Пользователь {message.from_user.username} написал: {message.text}')
    await message.answer(f'Ты написал: {message.text}')


async def main() -> None:
    await bot.set_my_commands(
        [
            BotCommand(command='start', description='Запустить бота'),
            BotCommand(command='card', description='Получить случайную карту'),
        ]
    )

    print('Bot запустился')
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())