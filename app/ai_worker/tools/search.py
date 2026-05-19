# app/ai_worker/tools/search.py
import os
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper
from langchain.tools import tool
from app.core.config import settings
from app.core.logging import logger

# Устанавливаем прокси для системного окружения, чтобы OpenAI и другие сервисы его видели
os.environ["HTTP_PROXY"] = settings.PROXY_URL
os.environ["HTTPS_PROXY"] = settings.PROXY_URL

def get_search_tool():
    """
    Фабрика для создания инструмента поиска.
    Настроена так, чтобы DuckDuckGo НЕ использовал прокси, даже если они заданы в системе.
    """
    # Создаем wrapper и принудительно отключаем прокси для DDG, 
    # если библиотека позволяет передать конфиг. 
    # Если нет - библиотека duckduckgo_search имеет свои механизмы.
    wrapper = DuckDuckGoSearchAPIWrapper(
        max_results=5,
        region="ru-ru",
        time="y"
    )
    
    # В новых версиях duckduckgo_search можно управлять прокси через переменные,
    # но самый верный способ для DDG - это использовать чистый запрос.
    search = DuckDuckGoSearchRun(api_wrapper=wrapper)
    return search

@tool
async def internet_search(query: str) -> str:
    """
    Поиск актуальной информации в интернете через DuckDuckGo без использования прокси. 
    """
    # Сохраняем старые значения прокси
    old_http = os.environ.get("HTTP_PROXY")
    old_https = os.environ.get("HTTPS_PROXY")
    
    try:
        # Временно удаляем прокси из окружения только на время вызова DDG
        if "HTTP_PROXY" in os.environ: del os.environ["HTTP_PROXY"]
        if "HTTPS_PROXY" in os.environ: del os.environ["HTTPS_PROXY"]
        
        logger.info(f"Tool: Searching internet (no-proxy) for query: '{query}'")
        search = get_search_tool()
        result = search.run(query)
        return result
    except Exception as e:
        logger.error(f"Error in internet_search tool: {e}")
        return f"К сожалению, во время поиска произошла ошибка: {str(e)}"
    finally:
        # Возвращаем прокси на место, чтобы OpenAI продолжал работать
        if old_http: os.environ["HTTP_PROXY"] = old_http
        if old_https: os.environ["HTTPS_PROXY"] = old_https