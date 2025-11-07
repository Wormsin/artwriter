# /api/Dockerfile

# 1. Берем базовый образ Python
FROM python:3.11-slim

# 2. Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# 3. Копируем файл с зависимостями
COPY requirements.txt .

# 4. Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# 5. Копируем весь код твоего API в контейнер
COPY . .

RUN mkdir -p /projects_root
RUN mkdir -p /logs

# 6. Команда для запуска твоего API
# Uvicorn будет слушать на 0.0.0.0, чтобы быть доступным
# извне контейнера. 8000 - стандартный порт.
#CMD ["python", "app/main.py", "--host", "127.0.0.1", "--port", "8000"]
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]