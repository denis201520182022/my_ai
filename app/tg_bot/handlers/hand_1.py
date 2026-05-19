# app/tg_bot/handlers/hand_1.py
import io
import json
import aiohttp
import aio_pika
from aiogram import Router, F, types
from aiogram.filters import Command
from sqlalchemy import select

from app.core.config import settings
from app.core.logging import logger
from app.core.rabbitmq import QUEUE_TG_TO_AI
from app.database.database import AsyncSessionLocal
from app.database.models import User

router = Router()

async def get_or_create_user(telegram_id: int, username: str = None):
    """Обеспечивает наличие пользователя в базе данных."""
    async with AsyncSessionLocal() as session:
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            user = User(telegram_id=telegram_id, username=username)
            session.add(user)
            await session.commit()
            logger.info(f"New user created: {telegram_id}")
        return user

async def send_to_ai_worker(payload: dict):
    """Отправляет упакованную задачу в очередь RabbitMQ."""
    connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
    async with connection:
        channel = await connection.channel()
        await channel.default_exchange.publish(
            aio_pika.Message(
                body=json.dumps(payload).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT  # Исправлено на PERSISTENT
            ),
            routing_key=QUEUE_TG_TO_AI
        )

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    await get_or_create_user(message.from_user.id, message.from_user.username)
    await message.answer("Привет! Я твой персональный ИИ-ассистент.\n\n"
                         "Я умею:\n"
                         "— Искать информацию в интернете\n"
                         "— Запоминать важные факты (скажи 'запомни...')\n"
                         "— Ставить напоминания\n"
                         "— Понимать голосовые сообщения")

@router.message(F.text | F.voice)
async def handle_all_messages(message: types.Message):
    # 1. Сразу проверяем/создаем юзера
    await get_or_create_user(message.from_user.id, message.from_user.username)
    
    user_text = ""
    
    # 2. Обработка голоса
    if message.voice:
        wait_msg = await message.answer("🔊 Расшифровываю голос...")
        try:
            # Получаем информацию о файле
            file_id = message.voice.file_id
            file = await message.bot.get_file(file_id)
            
            # Скачиваем файл в память (через прокси, т.к. сессия бота с прокси)
            voice_io = io.BytesIO()
            await message.bot.download_file(file.file_path, voice_io)
            voice_io.seek(0)

            # Отправляем в наш микросервис STT
            async with aiohttp.ClientSession() as session:
                form_data = aiohttp.FormData()
                form_data.add_field('file', voice_io, filename='voice.ogg')
                
                async with session.post(settings.STT_SERVICE_URL, data=form_data) as resp:
                    if resp.status == 200:
                        stt_data = await resp.json()
                        user_text = stt_data.get("text", "")
                        await wait_msg.edit_text(f"🎤 _Вы сказали:_ {user_text}", parse_mode="Markdown")
                    else:
                        await wait_msg.edit_text("❌ Ошибка при расшифровке голоса.")
                        return
        except Exception as e:
            logger.error(f"STT Error: {e}")
            await message.answer("❌ Произошла ошибка при обработке аудио.")
            return
    else:
        # Это обычный текст
        user_text = message.text

    if not user_text:
        return

    # 3. Формируем задачу для ИИ
    payload = {
        "chat_id": message.chat.id,
        "user_id": message.from_user.id,
        "text": user_text,
        "username": message.from_user.username,
        "message_id": message.message_id
    }

    # 4. Отправляем в RabbitMQ
    try:
        await send_to_ai_worker(payload)
        # Если это был текст, даем фидбек, что мы начали думать
        if not message.voice:
            await message.bot.send_chat_action(message.chat.id, "typing")
    except Exception as e:
        logger.error(f"RabbitMQ Publish Error: {e}")
        await message.answer("❌ Сервис временно недоступен (ошибка очереди).")