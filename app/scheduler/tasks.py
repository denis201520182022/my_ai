# app/scheduler/tasks.py
import asyncio
import datetime
import json
import aio_pika
from sqlalchemy import select
from app.scheduler.celery_app import celery_app
# Импортируем engine, чтобы иметь к нему доступ
from app.database.database import AsyncSessionLocal, engine 
from app.database.models import Reminder, User
from app.core.rabbitmq import QUEUE_AI_TO_TG
from app.core.config import settings
from app.core.logging import logger

async def _check_reminders_async():
    """Асинхронная логика проверки напоминаний"""
    try:
        async with AsyncSessionLocal() as session:
            now = datetime.datetime.utcnow()
            
            # 1. Ищем напоминания
            stmt = (
                select(Reminder, User.telegram_id)
                .join(User)
                .where(Reminder.remind_at <= now)
                .where(Reminder.is_triggered == False)
            )
            result = await session.execute(stmt)
            reminders_to_send = result.all()

            if not reminders_to_send:
                return

            # 2. Подключаемся к RabbitMQ
            connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
            async with connection:
                channel = await connection.channel()
                
                for reminder, tg_id in reminders_to_send:
                    payload = {
                        "chat_id": tg_id,
                        "text": f"🔔 **Напоминание:**\n{reminder.text}",
                        "type": "notification"
                    }
                    
                    await channel.default_exchange.publish(
                        aio_pika.Message(body=json.dumps(payload).encode()),
                        routing_key=QUEUE_AI_TO_TG
                    )
                    
                    reminder.is_triggered = True
                    logger.info(f"Reminder {reminder.id} sent to user {tg_id}")

                await session.commit()
    finally:
        # ПРИНУДИТЕЛЬНО закрываем все соединения пула в текущем Event Loop
        await engine.dispose()

@celery_app.task
def check_reminders():
    """Обертка для запуска асинхронного кода в Celery"""
    try:
        asyncio.run(_check_reminders_async())
    except Exception as e:
        logger.error(f"Error in check_reminders task: {e}")

@celery_app.task
def add_reminder_to_db(user_tg_id: int, text: str, remind_at_iso: str):
    """Эту задачу будет вызывать ИИ-агент через Tool."""
    async def _add():
        try:
            async with AsyncSessionLocal() as session:
                res = await session.execute(select(User).where(User.telegram_id == user_tg_id))
                user = res.scalar_one_or_none()
                
                if user:
                    new_reminder = Reminder(
                        user_id=user.id,
                        text=text,
                        remind_at=datetime.datetime.fromisoformat(remind_at_iso),
                        is_triggered=False
                    )
                    session.add(new_reminder)
                    await session.commit()
                    logger.info(f"Added reminder for user {user_tg_id} at {remind_at_iso}")
        finally:
            # ПРИНУДИТЕЛЬНО закрываем соединения пула в текущем Event Loop
            await engine.dispose()

    asyncio.run(_add())