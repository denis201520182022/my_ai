# app/tg_bot/main.py
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiohttp_socks import ProxyConnector

from app.core.config import settings
from app.core.logging import setup_logging, logger
from app.core.rabbitmq import init_queues
from app.tg_bot.middlewares import WhitelistMiddleware
from app.tg_bot.handlers.hand_1 import router as main_router
from app.tg_bot.consumer import start_consumer

async def main():
    # 1. Настройка логирования
    setup_logging()
    logger.info("Starting Telegram Bot interface...")

    # 2. Настройка прокси через aiohttp-socks (Твое требование в ТЗ)
    # Используем данные из .env для создания коннектора
    connector = ProxyConnector.from_url(settings.PROXY_URL)
    session = AiohttpSession(connector=connector)

    # 3. Инициализация Бота и Диспетчера
    # parse_mode="HTML" или "MarkdownV2" для красивых ответов от ИИ
    bot = Bot(token=settings.BOT_TOKEN, session=session)
    dp = Dispatcher()

    # 4. Подключение защиты (Whitelist)
    dp.message.middleware(WhitelistMiddleware())

    # 5. Регистрация роутеров с хэндлерами
    dp.include_router(main_router)

    # 6. Инициализация очередей RabbitMQ (создаем, если их нет)
    await init_queues()

    # 7. Запуск фоновой задачи: слушаем очередь ответов от ИИ
    # Мы передаем объект bot, чтобы консьюмер мог отправлять сообщения
    asyncio.create_task(start_consumer(bot))

    # 8. Запуск бесконечного цикла получения обновлений (Polling)
    logger.info("Bot is ready and polling...")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped")