# app/tg_bot/consumer.py
import json
import aio_pika
from aiogram import Bot
from app.core.config import settings
from app.core.rabbitmq import QUEUE_AI_TO_TG
from app.core.logging import logger

async def start_consumer(bot: Bot):
    """
    Слушает очередь ответов от ИИ (RabbitMQ) и отправляет их пользователям в TG.
    """
    # 1. Устанавливаем соединение с RabbitMQ
    connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
    
    async with connection:
        # 2. Создаем канал
        channel = await connection.channel()
        
        # Ограничиваем количество сообщений, обрабатываемых одновременно (QOS)
        await channel.set_qos(prefetch_count=10)

        # 3. Подключаемся к очереди
        queue = await channel.declare_queue(QUEUE_AI_TO_TG, durable=True)

        logger.info(f"Consumer started. Waiting for messages in {QUEUE_AI_TO_TG}...")

        # 4. Начинаем бесконечный цикл прослушивания
        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    try:
                        # Декодируем входящие данные
                        data = json.loads(message.body.decode())
                        chat_id = data.get("chat_id")
                        text = data.get("text")

                        if not chat_id or not text:
                            logger.error(f"Invalid message format in consumer: {data}")
                            continue

                        # 5. Отправляем сообщение пользователю
                        # Мы используем Bot, прокинутый из main.py (который работает через прокси)
                        await bot.send_message(
                            chat_id=chat_id,
                            text=text,
                            parse_mode="Markdown"  # Чтобы ответы ИИ (код, жирный шрифт) выглядели красиво
                        )
                        
                        logger.info(f"Successfully sent AI response to chat_id: {chat_id}")

                    except Exception as e:
                        logger.error(f"Error while sending message in consumer: {e}")