import logging
import sys
from app.core.config import settings

def setup_logging():
    # Уровни логирования: DEBUG, INFO, WARNING, ERROR, CRITICAL
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    # Настраиваем формат: Время - Имя модуля - Уровень - Сообщение
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)  # Вывод в консоль (Docker logs)
        ],
    )

    # Уменьшаем уровень шума от сторонних библиотек (если нужно)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    logging.getLogger("aiogram").setLevel(logging.INFO)

# Создаем глобальный логгер для быстрого доступа
logger = logging.getLogger("ai_agent")