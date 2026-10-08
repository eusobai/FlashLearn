# Обрабатывает ошибки Telegram, например,
# когда пользователь нажимает на устаревшую inline-кнопку.
from aiogram.exceptions import TelegramBadRequest

# Логгер проекта для записи информации и ошибок.
from utils.logger import logger



# Здесь временно хранится текущее слово для каждого пользователя,
# который проходит тест.
#
# current_quiz_words — текстовый тест.
# current_choice_quiz_words — тест с вариантами ответа.
current_quiz_words = {}
current_choice_quiz_words = {}

# Временная статистика активных тренировок: текстовых и с вариантами.
# Например:
# ative_quiz_stats[123] = {
#     "correct": 3,
#     "total": 5
# }
#
# Эта статистика не хранится в БД.
# Она нужна только пока пользователь проходит одну тренировку.
active_quiz_stats = {}

# Хранит последнее сообщение с вопросом тренировки каждого пользователя.
# Нужно, чтобы потом убрать с него кнопку «Завершить тренировку».
active_quiz_message = {}


# =========================
# ФУНКЦИИ ПОМОШНИКИ
# =========================

async def hide_active_quiz_keyboard(user_id: int) -> None:

    question_message = active_quiz_message.pop(user_id, None)
    
    if question_message is None:
        return
    
    try:
        await question_message.edit_reply_markup(reply_markup = None)

    except TelegramBadRequest as error: 
        logger.warning(
            "Failed to remove training buttons | user_id=%s | error=%s",
            user_id, error
        )


async def cancel_active_quiz(user_id) -> None:

    # Убираем кнопку со старого вопроса.
    await hide_active_quiz_keyboard(user_id)

    # Полностью очищаем временные данные старой тренировки.
    active_quiz_stats.pop(user_id, None)
    current_choice_quiz_words.pop(user_id, None)
    current_quiz_words.pop(user_id, None)

