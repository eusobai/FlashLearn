# =========================
# ИМПОРТЫ
# =========================


# Типы Telegram-объектов.
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Функции для работы с базой данных.
from database.database import get_levels_from_db, get_topics_in_db



def build_level_keyboard(levels) -> InlineKeyboardMarkup:
    rows = []
    for level in levels:
        rows.append(
            [InlineKeyboardButton(text=f"🎓 Уровень: {level['name']}", callback_data=f"level:{level['id']}")]
        )
        
    rows.append(
        [InlineKeyboardButton(text="❓ Узнать свой уровень:", callback_data="check_level")]
    )       
    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_mode_keyboard():

    mode_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎲 Случайные слова:", callback_data="")],
            [InlineKeyboardButton(text="📚 По темам:", callback_data="topic_words")]
        ]
    )

    return mode_keyboard


def build_topic_keyboard(topics) -> InlineKeyboardMarkup:
    rows = []

    for topic in topics:
        rows.append(
            [InlineKeyboardButton(text=f"💬 {topic['name']}")]
        )