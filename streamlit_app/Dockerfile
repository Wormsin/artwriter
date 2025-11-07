# /frontend/Dockerfile

# 1. Берем базовый образ Python
FROM python:3.11-slim

# 2. Устанавливаем рабочую директорию
WORKDIR /app

# 3. Копируем файл с зависимостями
COPY requirements.txt .

# 4. Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# 5. Копируем весь код Streamlit в контейнер
COPY . .

# 6. Открываем порт, на котором работает Streamlit (по умолчанию 8501)
EXPOSE 8501

# 7. Команда для запуска Streamlit
# --server.address=0.0.0.0 - обязательно, чтобы он был доступен
CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]