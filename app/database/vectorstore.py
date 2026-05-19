# app/database/vectorstore.py
import logging
from typing import List, Dict, Any
from sqlalchemy import select, and_
from langchain_huggingface import HuggingFaceEmbeddings

from app.database.models import VectorKnowledge, User
from app.core.config import settings
from app.core.logging import logger

class VectorStoreManager:
    def __init__(self):
        # Инициализируем локальную модель эмбеддингов
        # Она скачается при первом запуске и будет жить в Docker Volume (hf_cache)
        logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL_NAME}...")
        self.embeddings = HuggingFaceEmbeddings(
            model_name=settings.EMBEDDING_MODEL_NAME,
            model_kwargs={'device': 'cpu'}, # Используем CPU (бесплатно и доступно везде)
            encode_kwargs={'normalize_embeddings': True} # Важно для косинусного сходства
        )
        logger.info("Embedding model loaded successfully.")

    async def add_text(self, session, user_telegram_id: int, text: str, metadata: Dict[str, Any] = None):
        """
        Превращает текст в вектор и сохраняет в БД с привязкой к пользователю.
        """
        # 1. Получаем внутреннего user_id
        stmt = select(User.id).where(User.telegram_id == user_telegram_id)
        result = await session.execute(stmt)
        user_internal_id = result.scalar_one_or_none()

        if not user_internal_id:
            logger.error(f"User {user_telegram_id} not found in DB when adding knowledge")
            return

        # 2. Генерируем эмбеддинг (асинхронно через LangChain)
        vector = await self.embeddings.aembed_query(text)

        # 3. Сохраняем в базу
        new_knowledge = VectorKnowledge(
            user_id=user_internal_id,
            content=text,
            embedding=vector,
            metadata_=metadata or {}
        )
        session.add(new_knowledge)
        logger.info(f"Added new knowledge for user {user_telegram_id}")

    async def search_similar(self, session, user_telegram_id: int, query: str, limit: int = 3) -> List[str]:
        """
        Ищет наиболее похожие куски текста в памяти конкретного пользователя.
        """
        # 1. Получаем внутреннего user_id
        stmt_user = select(User.id).where(User.telegram_id == user_telegram_id)
        res_user = await session.execute(stmt_user)
        user_internal_id = res_user.scalar_one_or_none()

        if not user_internal_id:
            return []

        # 2. Генерируем вектор для поискового запроса
        query_vector = await self.embeddings.aembed_query(query)

        # 3. Выполняем поиск через pgvector (косинусное расстояние)
        # В SQLAlchemy для pgvector используется оператор .cosine_distance()
        stmt = (
            select(VectorKnowledge.content)
            .where(VectorKnowledge.user_id == user_internal_id)
            .order_by(VectorKnowledge.embedding.cosine_distance(query_vector))
            .limit(limit)
        )
        
        result = await session.execute(stmt)
        return [row[0] for row in result.all()]

# Создаем глобальный экземпляр менеджера
# Он загрузит модель один раз при импорте в ai-worker
vector_manager = VectorStoreManager()