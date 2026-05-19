# app/core/config.py
from typing import List
from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Указываем Pydantic, что нужно читать данные из файла .env
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8", 
        extra="ignore"
    )

    # --- PROXY ---
    SQUID_PROXY_HOST: str
    SQUID_PROXY_PORT: int
    SQUID_PROXY_USER: str
    SQUID_PROXY_PASSWORD: str
    PROXY_URL: str

    # --- TELEGRAM ---
    BOT_TOKEN: str
    ALLOWED_USERS: str  # В .env это строка "123,456", ниже превратим в список

    @computed_field
    @property
    def ALLOWED_USERS_LIST(self) -> List[int]:
        """Превращает строку из ALLOWED_USERS в список целых чисел (ID)."""
        if not self.ALLOWED_USERS:
            return []
        return [int(uid.strip()) for uid in self.ALLOWED_USERS.split(",") if uid.strip()]

    # --- LLM KEYS ---
    OPENAI_API_KEY: str | None = None
    OPENROUTER_API_KEY: str | None = None
    GOOGLE_API_KEY: str | None = None
    CURRENT_LLM_MODEL: str = "gpt-4o"

    # --- LANGFUSE ---
    LANGFUSE_PUBLIC_KEY: str
    LANGFUSE_SECRET_KEY: str
    LANGFUSE_HOST: str = "https://cloud.langfuse.com"

    # --- DATABASE (POSTGRES) ---
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    DATABASE_URL: str

    # --- RABBITMQ ---
    RABBITMQ_USER: str
    RABBITMQ_PASS: str
    RABBITMQ_HOST: str
    RABBITMQ_PORT: int
    RABBITMQ_URL: str

    # --- REDIS ---
    REDIS_HOST: str
    REDIS_PORT: int

    @computed_field
    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"

    # --- INTERNAL SERVICES ---
    STT_SERVICE_URL: str
    EMBEDDING_MODEL_NAME: str = "cointegrated/rubert-tiny2"

    # --- SYSTEM ---
    LOG_LEVEL: str = "INFO"
    MAX_AGENT_ITERATIONS: int = 10


# Создаем экземпляр настроек для использования в приложении
settings = Settings()