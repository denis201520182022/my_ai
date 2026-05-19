import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from app.database.models import Base
from app.core.config import settings
from app.core.logging import logger

async def init_models():
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    async with engine.begin() as conn:
        # Это создаст все таблицы и расширение pgvector, если их нет
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created successfully")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(init_models())