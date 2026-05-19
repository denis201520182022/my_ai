# stt_service/main.py
import os
import shutil
import uuid
from fastapi import FastAPI, UploadFile, File, HTTPException
from faster_whisper import WhisperModel

app = FastAPI(title="STT Whisper Service")

# Загружаем модель при старте. 
# "base" — золотая середина между скоростью и качеством. 
# Можно сменить на "tiny" (быстрее) или "small" (точнее).
MODEL_SIZE = "base"
device = "cpu" # Используем процессор

print(f"Loading Whisper model '{MODEL_SIZE}'...")
model = WhisperModel(MODEL_SIZE, device=device, compute_type="int8")
print("Model loaded successfully.")

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    # 1. Генерируем уникальное имя для временного файла
    temp_filename = f"temp_{uuid.uuid4()}.ogg"
    
    try:
        # 2. Сохраняем входящий поток байтов в файл
        with open(temp_filename, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 3. Запускаем транскрибацию
        # beam_size=5 — стандарт для хорошего качества
        segments, info = model.transcribe(temp_filename, beam_size=5, language="ru")

        # 4. Собираем текст из сегментов
        full_text = "".join([segment.text for segment in segments])

        return {
            "text": full_text.strip(),
            "language": info.language,
            "probability": info.language_probability
        }

    except Exception as e:
        print(f"Error during transcription: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        # 5. Обязательно удаляем временный файл
        if os.path.exists(temp_filename):
            os.remove(temp_filename)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)