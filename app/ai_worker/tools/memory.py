# app/ai_worker/tools/memory.py
from langchain.tools import tool
from langchain_core.runnables.config import RunnableConfig
from app.database.database import AsyncSessionLocal
from app.database.vectorstore import vector_manager
from app.core.logging import logger

@tool
async def save_to_memory(text: str, config: RunnableConfig) -> str:
    """
    Используй этот инструмент, чтобы навсегда запомнить важную информацию, которую предоставил пользователь.
    Вызывай его, если пользователь прямо просит "запомни это" или если он сообщает важные факты о себе 
    (имена, предпочтения, пароли, важные даты).
    Входной параметр: чистый текст для сохранения.
    """
    # Извлекаем user_id, который мы передали в конфиг при запуске графа
    user_id = config.get("configurable", {}).get("user_id")
    
    if not user_id:
        return "Ошибка: не удалось определить ID пользователя для сохранения."

    try:
        async with AsyncSessionLocal() as session:
            await vector_manager.add_text(
                session=session,
                user_telegram_id=int(user_id),
                text=text,
                metadata={"source": "manual_save"}
            )
            # Фиксируем изменения в базе
            await session.commit()
            
        logger.info(f"Tool: Information saved to memory for user {user_id}")
        return f"Я успешно запомнил информацию: '{text}'"
    except Exception as e:
        logger.error(f"Error in save_to_memory tool: {e}")
        return f"Произошла ошибка при попытке сохранить информацию: {str(e)}"

@tool
async def search_memory(query: str, config: RunnableConfig) -> str:
    """
    Используй этот инструмент, чтобы найти информацию в личной памяти пользователя.
    Вызывай его, если пользователь задает вопросы типа "что я тебе говорил про...", "ты помнишь мой...", 
    "найди в моих записях". 
    Входной параметр: поисковый запрос (ключевые слова).
    """
    user_id = config.get("configurable", {}).get("user_id")
    
    if not user_id:
        return "Ошибка: не удалось определить ID пользователя для поиска."

    try:
        async with AsyncSessionLocal() as session:
            # Ищем топ-3 похожих записи
            results = await vector_manager.search_similar(
                session=session,
                user_telegram_id=int(user_id),
                query=query,
                limit=3
            )
            
        if not results:
            logger.info(f"Tool: Search in memory for user {user_id} returned no results")
            return "В моей памяти ничего не найдено по этому запросу."

        # Формируем красивый список найденных фактов
        formatted_results = "\n".join([f"- {r}" for r in results])
        logger.info(f"Tool: Found {len(results)} relevant records in memory for user {user_id}")
        return f"Вот что я нашел в твоих записях:\n{formatted_results}"

    except Exception as e:
        logger.error(f"Error in search_memory tool: {e}")
        return f"Произошла ошибка при поиске в памяти: {str(e)}"