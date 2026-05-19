# app/ai_worker/tools/reminder.py
import datetime
from langchain.tools import tool
from langchain_core.runnables.config import RunnableConfig
from app.scheduler.tasks import add_reminder_to_db
from app.core.logging import logger

@tool
async def set_reminder(datetime_iso: str, reminder_text: str, config: RunnableConfig) -> str:
    """
    Используй этот инструмент для создания напоминаний. 
    Параметры:
    - datetime_iso: строка в формате ISO 8601 (ГГГГ-ММ-ДДTЧЧ:ММ:СС), когда нужно прислать уведомление.
    - reminder_text: текст того, о чем нужно напомнить.
    
    Важно: Вычисляй точное время на основе текущей даты и времени, которые даны тебе в системных инструкциях.
    """
    user_id = config.get("configurable", {}).get("user_id")
    
    if not user_id:
        return "Ошибка: не удалось определить ID пользователя для создания напоминания."

    try:
        # Валидация формата даты
        remind_at = datetime.datetime.fromisoformat(datetime_iso)
        
        # Проверка, не в прошлом ли это время (с учетом UTC)
        now = datetime.datetime.utcnow()
        if remind_at < now:
            return f"Ошибка: указанное время {datetime_iso} уже прошло. Сейчас {now.isoformat()}. Пожалуйста, укажи время в будущем."

        # Отправляем задачу в Celery воркер (метод .delay отправляет задачу в RabbitMQ)
        add_reminder_to_db.delay(
            user_tg_id=int(user_id),
            text=reminder_text,
            remind_at_iso=datetime_iso
        )

        logger.info(f"Tool: Reminder set for user {user_id} at {datetime_iso}")
        
        # Форматируем для ответа пользователю (красивый вид)
        readable_time = remind_at.strftime("%d.%m.%Y в %H:%M")
        return f"Окей, я напомню тебе '{reminder_text}' точно в {readable_time}."

    except ValueError:
        logger.error(f"Tool Error: Invalid date format received from LLM: {datetime_iso}")
        return "Ошибка: неверный формат даты. Пожалуйста, используй формат ISO (ГГГГ-ММ-ДДTЧЧ:ММ:СС)."
    except Exception as e:
        logger.error(f"Error in set_reminder tool: {e}")
        return f"Произошла техническая ошибка при создании напоминания: {str(e)}"