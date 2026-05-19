# app/core/rabbitmq.py
import aio_pika
from app.core.config import settings
from app.core.logging import logger

# Константы для названий очередей, чтобы не ошибиться в воркерах
QUEUE_TG_TO_AI = "tg_to_ai_tasks"  # Бот -> ИИ Воркер
QUEUE_AI_TO_TG = "ai_to_tg_answers" # ИИ Воркер -> Бот

async def get_rabbitmq_connection():
    """Устанавливает устойчивое (robust) соединение с RabbitMQ"""
    try:
        connection = await aio_pika.connect_robust(
            settings.RABBITMQ_URL,
            timeout=20
        )
        logger.info("Successfully connected to RabbitMQ")
        return connection
    except Exception as e:
        logger.error(f"Failed to connect to RabbitMQ: {e}")
        raise

async def init_queues():
    """Инициализация очередей (создает их, если они еще не существуют)"""
    connection = await get_rabbitmq_connection()
    async with connection:
        channel = await connection.channel()
        
        # durable=True гарантирует, что очереди не пропадут при перезагрузке RabbitMQ
        await channel.declare_queue(QUEUE_TG_TO_AI, durable=True)
        await channel.declare_queue(QUEUE_AI_TO_TG, durable=True)
        
        logger.info("RabbitMQ queues initialized")