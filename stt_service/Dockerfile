# stt_service/Dockerfile
# Используем Python 3.10-slim для уменьшения размера образа
FROM python:3.10-slim

# Устанавливаем ffmpeg, так как whisper работает с аудио через него
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код
COPY main.py .

# Открываем порт
EXPOSE 8000

# Запускаем сервис
CMD ["python", "main.py"]