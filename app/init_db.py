import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
# УБРАЛИ "app." из импортов, так как файл уже внутри этой папки
from database.models import Base 
from core.config import settings
from core.logging import logger

async def init_models():
    # Создаем движок
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    async with engine.begin() as conn:
        # Сначала создаем расширение (нужны права суперпользователя в БД)
        await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
        # Создаем таблицы
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created successfully")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(init_models())