# app/core/redis.py
from redis.asyncio import Redis
from app.core.config import settings

# decode_responses=True автоматически превращает байты в строки (utf-8)
redis_client = Redis.from_url(
    settings.REDIS_URL, 
    decode_responses=True
)

async def get_redis_client() -> Redis:
    """Функция для получения клиента (полезно для Dependency Injection)"""
    return redis_client