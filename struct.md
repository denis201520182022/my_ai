ai_agent_project/
├── .env                          # Все секреты, ключи (LLM, Langfuse), пароли от БД и настройки прокси
├── docker-compose.yml            # Инфраструктура (Postgres, RabbitMQ, 4 наших контейнера)
├── .gitignore                    # Исключения для Git (чтобы не запушить .env и кэши)
├── .dockerignore
│
├── stt_service/                  # Изолированный микросервис для локальной расшифровки голоса
│   ├── Dockerfile
│   ├── requirements.txt          # Зависимости: fastapi, uvicorn, faster-whisper
│   └── main.py                   # API, принимающее аудио и возвращающее текст
│
└── app/                          # Главная директория (общий код для бота, ИИ и планировщика)
    ├── Dockerfile                # Единый докерфайл для 3-х воркеров (запускаются разными командами)
    ├── requirements.txt          # Зависимости: aiogram, langchain, celery, asyncpg, sentence-transformers
    │
    ├── core/                     # Ядро: общие настройки и подключения
    │   ├── config.py             # Чтение .env (Pydantic Settings)
    │   ├── rabbitmq.py           # Настройки подключения и очередей RabbitMQ
    │   ├── redis.py              # Настройка подключения к редис
    │
    ├── database/                 # Работа с БД (PostgreSQL + pgvector)
    │   ├── database.py           # Подключение к БД (SQLAlchemy / asyncpg)
    │   ├── models.py             # Таблицы (пользователи, история сообщений, векторное хранилище)
    │   └── vectorstore.py        # Логика RAG с использованием локальной rubert-tiny2
    │
    ├── tg_bot/                   # Воркер 1: Telegram Бот (Интерфейс)
    │   ├── main.py               # Точка входа бота (запуск aiogram)
    │   ├── middlewares.py        # Защита: проверка на разрешенных пользователей (Whitelist)
    │   ├── handlers/          
        |   ├── hand_1.py       # Обработка текста и голоса (отправка аудио в stt_service и задач в RabbitMQ)
    │   └── consumer.py           # Прослушивание ответов от ИИ из RabbitMQ для отправки юзеру
    │
    ├── ai_worker/                # Воркер 2: ИИ Движок (Мозг)
    │   ├── main.py               # Точка входа: чтение задач из RabbitMQ
    │   ├── graph.py              # Логика LangGraph: State, Nodes, Edges, ReAct циклы
    │   ├── agent.py              # Инициализация LLM с подключением Langfuse
    │   └── tools/                # Инструменты для агента
    │       ├── search.py         # Поиск в интернете (DuckDuckGo через прокси)
    │       ├── memory.py         # Инструменты для сохранения/чтения из RAG (pgvector)
    │       └── reminder.py       # Инструмент, который ставит задачу в Celery
    │
    └── scheduler/                # Воркер 3: Планировщик напоминаний
        ├── celery_app.py         # Инициализация Celery (использует RabbitMQ как брокер)
        └── tasks.py              # Задача: дождаться времени -> сгенерировать алерт -> отправить боту