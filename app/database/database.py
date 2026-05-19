# app/database/database.py
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool
from app.core.config import settings

# Создаем асинхронный движок (Engine)
# Используем NullPool, так как в Celery-воркерах и разных потоках 
# общие соединения в пуле могут вызывать ошибку "Event loop is closed"
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    poolclass=NullPool,
)

# Фабрика сессий. expire_on_commit=False нужен для асинхронной работы, 
# чтобы объекты не "пропадали" после коммита
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

# Базовый класс для всех моделей
class Base(DeclarativeBase):
    pass

# Вспомогательная функция (генератор) для получения сессии БД
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()