# =========================
# ИМПОРТЫ
# =========================


# Типы Telegram-объектов.
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Функции для работы с базой данных.
from database.database import get_levels_from_db



def build_level_keyboard(levels) -> InlineKeyboardMarkup:
    rows = []
    for level in levels:
        rows.append(
            [InlineKeyboardButton(text=f"🎓 Уровень: {level['name']}", callback_data=f"level:{level['id']}")]
        )
        
    rows.append(
        [InlineKeyboardButton(text="❓ Узнать свой уровень:", callback_data="level:check_level")]
    )       
    return InlineKeyboardMarkup(inline_keyboard=rows)

