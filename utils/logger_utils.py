# =========================
# ИМПОРТЫ
# =========================

from pathlib import Path
import logging

# Получаем путь к папке, где находится main.py.
BASE_DIR = Path(__file__).resolve().parent.parent

# Создаём папку для логов.
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

# =========================
# НАСТРОЙКА ЛОГИРОВАНИЯ
# =========================
logging.basicConfig(
    level = logging.INFO,
    format = "%(asctime)s | %(levelname)s %(name)s %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "bot.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)

logging.getLogger('aiogram').setLevel(logging.WARNING)

# Создаём logger для записи событий работы бота.
logger = logging.getLogger(__name__)

