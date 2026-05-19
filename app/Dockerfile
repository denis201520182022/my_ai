FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# Указываем корень как путь поиска модулей
ENV PYTHONPATH=/

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Создаем рабочую директорию НЕ в /app
WORKDIR /

# Сначала ставим тяжелый torch (CPU версия)
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Копируем requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем проект ВНУТРЬ папки /app
# Теперь путь /app/database/... будет соответствовать импорту "from app.database"
COPY . /app

# Директория по умолчанию теперь внутри проекта
WORKDIR /app