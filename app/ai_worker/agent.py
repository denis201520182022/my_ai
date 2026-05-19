# app/ai_worker/agent.py
import httpx
from langchain_openai import ChatOpenAI
from langfuse.callback import CallbackHandler
from app.core.config import settings
from app.core.logging import logger

# Импортируем наши инструменты
from app.ai_worker.tools.search import internet_search
from app.ai_worker.tools.memory import save_to_memory, search_memory
from app.ai_worker.tools.reminder import set_reminder

def get_llm():
    """
    Конфигурирует и возвращает объект LLM с поддержкой прокси и инструментов.
    """
    
    # 1. Настройка прокси через httpx клиент
    # Это гарантирует, что запросы к OpenAI/OpenRouter пойдут через твой Squid
    proxy_mounts = {
        "all://": httpx.HTTPTransport(proxy=settings.PROXY_URL)
    }
    http_client = httpx.AsyncClient(mounts=proxy_mounts)

    # 2. Определяем параметры подключения
    # Если в модели есть слэш (например, 'anthropic/claude-3'), значит это OpenRouter
    is_openrouter = "/" in settings.CURRENT_LLM_MODEL
    base_url = "https://openrouter.ai/api/v1" if is_openrouter else None
    api_key = settings.OPENROUTER_API_KEY if is_openrouter else settings.OPENAI_API_KEY

    if not api_key:
        logger.error("LLM API Key is missing! Check your .env file.")
        raise ValueError("LLM API Key is missing")

    # 3. Инициализация модели
    llm = ChatOpenAI(
        model=settings.CURRENT_LLM_MODEL,
        openai_api_key=api_key,
        base_url=base_url,
        temperature=0.3, # Низкая температура для более точного следования инструкциям
        max_retries=3,
        http_async_client=http_client, # Прокидываем наш прокси-клиент
        streaming=False # Для воркера в очереди стриминг обычно не нужен
    )

    # 4. Привязываем инструменты к модели (Bind Tools)
    # Теперь LLM "знает", что она может вызывать эти функции
    tools = [internet_search, save_to_memory, search_memory, set_reminder]
    llm_with_tools = llm.bind_tools(tools)
    
    return llm_with_tools

def get_langfuse_callback():
    """
    Инициализирует CallbackHandler для мониторинга в Langfuse.
    Позволяет отслеживать латенси, токены и стоимость каждого шага.
    """
    if not settings.LANGFUSE_PUBLIC_KEY or not settings.LANGFUSE_SECRET_KEY:
        logger.warning("Langfuse keys are missing. Tracing is disabled.")
        return None
        
    return CallbackHandler(
        public_key=settings.LANGFUSE_PUBLIC_KEY,
        secret_key=settings.LANGFUSE_SECRET_KEY,
        host=settings.LANGFUSE_HOST
    )

# Экспортируем список инструментов для использования в графе
tools_list = [internet_search, save_to_memory, search_memory, set_reminder]