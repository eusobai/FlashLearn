import os
import asyncio

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message

from dotenv import load_dotenv
load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise RuntimeError('Не найден BOT_TOKEN. Добавь его в файл .env')


bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


@dp.message(CommandStart())
async def cmd_start(message: Message) -> None:
    await message.answer('Привет! Я помогу тебе учить английский: карточки, игра на совпадение и тесты.')


@dp.message()
async def echo_text(message: Message) -> None:
    print(f'(log) Пользователь {message.from_user.username} написал: {message.text}')
    await message.answer(f'Ты написал: {message.text}')


async def main() -> None:
    print('Bot запустился')
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())