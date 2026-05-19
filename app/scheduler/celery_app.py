# app/scheduler/celery_app.py
from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

# Создаем экземпляр Celery
celery_app = Celery(
    "agent_scheduler",
    broker=settings.RABBITMQ_URL,
    backend=settings.REDIS_URL,
    include=["app.scheduler.tasks"]  # Где искать задачи
)

# Настройки Celery
celery_app.conf.update(
    timezone="Europe/Moscow",
    enable_utc=True,
    task_track_started=True,
    # Настройка периодических задач (Beat)
    beat_schedule={
        "check-reminders-every-minute": {
            "task": "app.scheduler.tasks.check_reminders",
            "schedule": crontab(minute="*"),  # Запуск каждую минуту
        },
    },
)