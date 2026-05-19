# app/tg_bot/middlewares.py
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message
from app.core.config import settings
from app.core.logging import logger

class WhitelistMiddleware(BaseMiddleware):
    """
    Промежуточный слой для проверки доступа.
    Пропускает сообщения только от пользователей, ID которых есть в ALLOWED_USERS.
    """
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        # Проверяем только сообщения (Message)
        if not isinstance(event, Message):
            return await handler(event, data)

        user_id = event.from_user.id
        
        # Сверяем ID со списком из настроек
        if user_id not in settings.ALLOWED_USERS_LIST:
            logger.warning(f"Access denied for user_id: {user_id} (not in whitelist)")
            # Опционально: можно ответить пользователю, что доступа нет
            # Но для приватных ботов лучше просто игнорировать (drop)
            return 

        # Если пользователь в списке — продолжаем выполнение (передаем в хэндлер)
        return await handler(event, data)