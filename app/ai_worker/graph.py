# app/ai_worker/graph.py
import datetime
from typing import Annotated, TypedDict, Union
from pathlib import Path

from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langchain_core.messages import SystemMessage, HumanMessage

from app.ai_worker.agent import get_llm, tools_list
from app.core.config import settings
from app.core.logging import logger

# 1. Определяем состояние (State)
class AgentState(TypedDict):
    # add_messages позволяет накапливать историю, а не перезаписывать её
    messages: Annotated[list, add_messages]
    user_id: int

# 2. Функция загрузки системного промпта
def get_system_prompt():
    prompt_path = Path(__file__).parent / "prompts" / "system_prompt.md"
    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            template = f.read()
        
        # Динамически подставляем время
        now = datetime.datetime.now()
        return template.format(
            current_time=now.strftime("%Y-%m-%d %H:%M:%S"),
            day_of_week=now.strftime("%A")
        )
    except Exception as e:
        logger.error(f"Error loading system prompt: {e}")
        return "Ты — полезный ассистент."

# 3. Узел вызова модели
async def call_model(state: AgentState):
    prompt = get_system_prompt()
    messages = [SystemMessage(content=prompt)] + state["messages"]
    
    llm = get_llm()
    # Передаем user_id в конфиг для инструментов (memory, reminder)
    config = {"configurable": {"user_id": state["user_id"]}}
    
    response = await llm.ainvoke(messages, config=config)
    return {"messages": [response]}

# 4. Логика перехода (Router)
def should_continue(state: AgentState):
    last_message = state["messages"][-1]
    # Если модель вызвала инструменты — идем в узел action
    if last_message.tool_calls:
        return "action"
    # Если инструментов нет — завершаем работу и отвечаем юзеру
    return END

# 5. Сборка графа
def create_graph():
    workflow = StateGraph(AgentState)

    # Добавляем узлы
    workflow.add_node("agent", call_model)
    workflow.add_node("action", ToolNode(tools_list))

    # Устанавливаем точку входа
    workflow.set_entry_point("agent")

    # Добавляем условные переходы (ReAct цикл)
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "action": "action",
            END: END
        }
    )

    # После выполнения инструментов всегда возвращаемся к агенту для анализа результата
    workflow.add_edge("action", "agent")

    return workflow.compile()

# Инициализируем скомпилированный граф
app_graph = create_graph()