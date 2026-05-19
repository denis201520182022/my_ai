# app/Dockerfile
# Используем стабильную версию Python 3.11 на базе Debian (slim) для баланса веса и возможностей
FROM python:3.11-slim

# Настройка системных переменных для Python:
# Не создавать .pyc файлы, не буферизовать вывод (логи сразу видны)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Устанавливаем системные зависимости для работы с БД и сборки пакетов
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Создаем рабочую директорию
WORKDIR /app

# Сначала копируем только requirements.txt, чтобы закэшировать установку библиотек
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Копируем весь остальной код приложения
COPY . .

# Проверяем наличие папки для миграций (на случай если alembic еще не инициализирован)
RUN mkdir -p /app/migrations

# Этот Dockerfile универсальный — команда запуска будет переопределена 
# в docker-compose для каждого сервиса (bot, worker, scheduler)