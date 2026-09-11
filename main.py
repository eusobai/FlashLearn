import os
import asyncio
import random
import logging
from pathlib import Path

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command 
from aiogram.types import Message, BotCommand, KeyboardButton, ReplyKeyboardMarkup

from dotenv import load_dotenv
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
LOG_DIR = BASE_DIR / 'logs'
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level= logging.INFO,
    format= '%(asctime)s | %(levelname)s %(name)s %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / 'bot.log', encoding = 'utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

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

current_quiz_words = {}

main_keybord = ReplyKeyboardMarkup(
    keyboard=
        [ 
        [KeyboardButton(text='📚 Получить карточку')],
        [KeyboardButton(text = '📝 Пройти тест')]
        ],
    resize_keyboard = True,
    input_field_placeholder = 'Выбери действие',

)

@dp.message(CommandStart())
async def cmd_start(message: Message) -> None:
    username = message.from_user.username if message.from_user.username else 'unknown'
    logger.info(
        'The user is connected | username = %s', username
    )
    await message.answer(
        'Привет! Я помогу тебе учить английский.\n\n'
        'Выбери действие ниже:\n'
        '— Получить карточку\n'
        '— Пройти тест',
        reply_markup= main_keybord, 
    )


@dp.message(Command('card'))
@dp.message(F.text == '📚 Получить карточку')
async def send_card(message: Message) -> None:
    word = random.choice(WORDS)
    username = message.from_user.username if message.from_user.username else 'unknown'

    logger.info(
        'Card sent | username = %s | word = %s',
        username,
        word["english"]
    )
    await message.answer(
        f'📚 Карточка\n\n'
        f'Английское слово: {word['english']}\n'
        f'Перевод: {word['russian']}'
    )


@dp.message(Command('quiz'))
@dp.message(F.text =='📝 Пройти тест')
async def start_quiz(message: Message) -> None:
    user_id = message.from_user.id if message.from_user.id else 'unknown_id'
    word = random.choice(WORDS)

    current_quiz_words[user_id] = word

    logger.info(
        'Quiz started | user_id=%s | word=%s',
        user_id, word
    )

    await message.answer(
        f'📝 Как переводиться слово: {word['english']}?'
    )


@dp.message(F.text)
async def handle_text(message: Message) -> None:
    username = message.from_user.username if message.from_user.username else 'unknown'
    user_id = message.from_user.id if message.from_user.id else 'unknown_id'
    text = message.text.strip()

    if user_id in current_quiz_words:
        word = current_quiz_words.pop(user_id)
        is_correct = text.lower() == word['russian'].lower()

        logger.info(
            "Quiz answered | user_id=%s | correct=%s",
            user_id,
            is_correct,
        )

        if is_correct:

            await message.answer('✅ Правильно! Молодец.')
        else:
            await message.answer(f'❌ Пока нет. Правильный ответ: {word['russian']}')

        return
    
    logger.info(
        'Text received | username = %s | text = %s',
        username,
        text    
    )

    await message.answer(f'Ты написал: {message.text}')


async def main() -> None:
    await bot.set_my_commands(
        [
            BotCommand(command='start', description='Запустить бота'),
            BotCommand(command='card', description='Получить случайную карту'),
            BotCommand(command='quiz',description='Проверить перевод слова')
        ]
    )

    logger.info('Bot запустился')
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())