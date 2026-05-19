# app/tg_bot/main.py
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession

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

    # 2. Настройка прокси
    # Передаем proxy напрямую в AiohttpSession. 
    # Если URL начинается с socks5:// или socks4://, aiogram автоматически применит aiohttp-socks.
    session = None
    if settings.PROXY_URL:
        session = AiohttpSession(proxy=settings.PROXY_URL)
        logger.info(f"Telegram-бот запущен через прокси: {settings.PROXY_URL}")
    else:
        logger.info("Telegram-бот запущен без прокси")

    # 3. Инициализация Бота и Диспетчера
    bot = Bot(token=settings.BOT_TOKEN, session=session)
    dp = Dispatcher()

    # 4. Подключение защиты (Whitelist)
    dp.message.middleware(WhitelistMiddleware())

    # 5. Регистрация роутеров с хэндлерами
    dp.include_router(main_router)

    # 6. Инициализация очередей RabbitMQ (создаем, если их нет)
    await init_queues()

    # 7. Запуск фоновой задачи: слушаем очередь ответов от ИИ
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