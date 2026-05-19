# app/ai_worker/main.py
import json
import asyncio
import aio_pika
from sqlalchemy import select, insert
from langchain_core.messages import HumanMessage, AIMessage

from app.core.config import settings
from app.core.logging import logger, setup_logging
from app.core.rabbitmq import QUEUE_TG_TO_AI, QUEUE_AI_TO_TG
from app.database.database import AsyncSessionLocal
from app.database.models import ChatMessage, User
from app.ai_worker.graph import app_graph
from app.ai_worker.agent import get_langfuse_callback

setup_logging()

async def get_chat_history(session, user_id: int, limit: int = 10):
    """Загружает последние сообщения из БД и конвертирует их в формат LangChain."""
    stmt = (
        select(ChatMessage)
        .where(ChatMessage.user_id == user_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(limit)
    )
    result = await session.execute(stmt)
    messages = result.scalars().all()
    
    history = []
    # Разворачиваем, чтобы был хронологический порядок (старые в начале)
    for msg in reversed(messages):
        if msg.role == "user":
            history.append(HumanMessage(content=msg.content))
        else:
            history.append(AIMessage(content=msg.content))
    return history

async def save_message(session, user_id: int, role: str, content: str):
    """Сохраняет новое сообщение в историю диалога."""
    new_msg = ChatMessage(
        user_id=user_id,
        role=role,
        content=content,
        session_id="default" # Можно расширить до разных сессий
    )
    session.add(new_msg)
    await session.commit()

async def process_task(message: aio_pika.IncomingMessage):
    """Основной цикл обработки одной задачи от пользователя."""
    async with message.process():
        data = json.loads(message.body.decode())
        chat_id = data["chat_id"]
        user_tg_id = data["user_id"]
        user_text = data["text"]

        async with AsyncSessionLocal() as db_session:
            # 1. Получаем внутреннего юзера
            stmt = select(User).where(User.telegram_id == user_tg_id)
            res = await db_session.execute(stmt)
            user = res.scalar_one_or_none()
            if not user:
                logger.error(f"User {user_tg_id} not found in database")
                return

            # 2. Сохраняем входящее сообщение пользователя
            await save_message(db_session, user.id, "user", user_text)

            # 3. Подгружаем историю (контекст)
            history = await get_chat_history(db_session, user.id)

            # 4. Запускаем LangGraph
            logger.info(f"AI Worker: Thinking for user {user_tg_id}...")
            
            # Настройка мониторинга Langfuse
            langfuse_handler = get_langfuse_callback()
            callbacks = [langfuse_handler] if langfuse_handler else []

            # Конфигурация для графа (передаем user_id для инструментов)
            config = {
                "configurable": {"user_id": user_tg_id},
                "callbacks": callbacks,
                "recursion_limit": settings.MAX_AGENT_ITERATIONS
            }

            try:
                # Запуск цикла размышлений ReAct
                result = await app_graph.ainvoke(
                    {"messages": history + [HumanMessage(content=user_text)], "user_id": user_tg_id},
                    config=config
                )

                # 5. Получаем финальный ответ от агента
                ai_response = result["messages"][-1].content

                # 6. Сохраняем ответ ИИ в БД
                await save_message(db_session, user.id, "assistant", ai_response)

                # 7. Отправляем результат обратно в RabbitMQ для ТГ-бота
                connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
                async with connection:
                    channel = await connection.channel()
                    response_payload = {
                        "chat_id": chat_id,
                        "text": ai_response
                    }
                    await channel.default_exchange.publish(
                        aio_pika.Message(body=json.dumps(response_payload).encode()),
                        routing_key=QUEUE_AI_TO_TG
                    )
                logger.info(f"AI Worker: Success response sent to {chat_id}")

            except Exception as e:
                logger.error(f"Error during AI processing: {e}")
                # Отправляем сообщение об ошибке пользователю
                # (здесь можно добавить логику уведомления в ТГ об ошибке)

async def main():
    """Запуск воркера."""
    logger.info("AI Worker is starting...")
    connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
    
    channel = await connection.channel()
    await channel.set_qos(prefetch_count=1) # Берем по одной задаче на воркер
    
    queue = await channel.declare_queue(QUEUE_TG_TO_AI, durable=True)
    
    logger.info(f"AI Worker is ready. Listening queue: {QUEUE_TG_TO_AI}")
    await queue.consume(process_task)

    # Держим воркер запущенным
    try:
        await asyncio.Future()
    finally:
        await connection.close()

if __name__ == "__main__":
    asyncio.run(main())