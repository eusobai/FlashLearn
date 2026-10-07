
# Типы Telegram-объектов:
from aiogram.types import CallbackQuery

# Обрабатывает ошибки Telegram, например,
# когда пользователь нажимает на устаревшую inline-кнопку.
from aiogram.exceptions import TelegramBadRequest

# Логгер проекта для записи информации и ошибок.
from utils.logger import logger


# Безопасно подтверждает нажатие inline-кнопки.
# Это нужно делать сразу, чтобы у пользователя не крутилась загрузка.
async def safe_callback_answer(callback: CallbackQuery, text: str = "") -> None:
    try:
        await callback.answer(text = text)  # сразу останавливает загрузку кнопки
    except TelegramBadRequest as error:
        # Такая ошибка возникает, если нажатие слишком старое:
        # например, сервер временно не мог связаться с Telegram.
        if "query is too old" in str(error):
            logger.warning(
                "Старое нажатие кнопки пропущено | user_id=%s",
                callback.from_user.id,
            )
        else:
            # Другие ошибки не скрываем — их нужно видеть в логах.
            raise
