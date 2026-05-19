# app/ai_worker/tools/search.py
import os
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper
from langchain.tools import tool
from app.core.config import settings
from app.core.logging import logger

def get_search_tool():
    """
    Фабрика для создания инструмента поиска.
    Использует API Wrapper с ограничением количества результатов для экономии контекста.
    """
    wrapper = DuckDuckGoSearchAPIWrapper(
        max_results=5,
        region="ru-ru",
        time="y" # Поиск за последний год для актуальности
    )
    
    # Создаем стандартный объект поиска
    search = DuckDuckGoSearchRun(api_wrapper=wrapper)
    return search

@tool
async def internet_search(query: str) -> str:
    """
    Поиск актуальной информации в интернете через DuckDuckGo. 
    Используй этот инструмент, когда пользователю нужно узнать свежие новости, 
    факты, цены или любую информацию, которой может не быть в твоих внутренних знаниях.
    Входной параметр: поисковый запрос.
    """
    try:
        logger.info(f"Tool: Searching internet for query: '{query}'")
        search = get_search_tool()
        # Запускаем поиск (библиотека работает синхронно, поэтому вызываем аккуратно)
        result = search.run(query)
        return result
    except Exception as e:
        logger.error(f"Error in internet_search tool: {e}")
        return f"К сожалению, во время поиска произошла ошибка: {str(e)}"