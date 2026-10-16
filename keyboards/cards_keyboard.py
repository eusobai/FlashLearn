# =========================
# ИМПОРТЫ
# =========================


# Типы Telegram-объектов.
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# 
from aiogram.utils.keyboard import InlineKeyboardBuilder

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
            [InlineKeyboardButton(text="🎲 Любые слова:", callback_data="random_words")],
            [InlineKeyboardButton(text="📚 По темам:", callback_data="topic_words")],
            [InlineKeyboardButton(text="🎓 Случайные слова по уровню:", callback_data="random_words_by_level")],
        ]
    )

    return mode_keyboard


def build_topic_keyboard(topics) -> InlineKeyboardMarkup:

    builder = InlineKeyboardBuilder()
    # Словарь сопоставления тем и смайлов (можно искать по названию или по ID)
    TOPIC_EMOJIS = {
        "food": "🍔",
        "travel": "✈️",
        "daily life": "🏡",
        "education": "📚",
        "work": "💼",
        "technology": "💻",
        "anthropology": "🪶",
        "art and architecture": "🏛️",
        "astronomy and physics": "🪐",
        "biology and life sciences": "🧬",
        "campus life": "🏫"
    }
    
    rows = []

    for topic in topics:
        topic_name = topic['name']
        # Приводим к нижнему регистру для точного совпадения со словарём
        clean_name = topic_name.lower().strip()
        
        # Ищем смайл в словаре. Если не нашли — ставим дефолтный 🏷️
        emoji = TOPIC_EMOJIS.get(clean_name, "🏷️")
        
        builder.add(
            InlineKeyboardButton(
                text=f"{emoji}  {topic_name}", 
                callback_data=f"topic:{topic['id']}"
            )
        )

   
    builder.adjust(2)

    print(builder)
    return builder.as_markup()

