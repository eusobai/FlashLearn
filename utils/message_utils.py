from aiogram.types import Message, InlineKeyboardMarkup

from aiogram.exceptions import TelegramBadRequest


async def clear_old_buttons(message: Message) -> None:

    # Оставляем только строки, в которых есть кнопка избранного.
    favourite_rows = []


    for row in message.reply_markup.inline_keyboard:
        has_favourite = False
        for button in row:
            
            # callback_data может быть пустым (например, у кнопки-ссылки).
            if(button.callback_data and button.callback_data.startswith("favourite:")):
                has_favourite = True
        
        if has_favourite:
            favourite_rows.append(row)

            
    # Если таких строк нет, это экран выбора: клавиатура убирается совсем.
    new_markup = InlineKeyboardMarkup(inline_keyboard=favourite_rows) if favourite_rows else None

    try:
        await message.edit_reply_markup(reply_markup=new_markup) 

    except TelegramBadRequest:
        # Сообщение удалено или кнопки уже убраны — это не ошибка.
        pass
