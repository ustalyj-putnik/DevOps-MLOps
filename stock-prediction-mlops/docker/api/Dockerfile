FROM python:3.10-slim
WORKDIR /app

# Устанавливаем зависимости
COPY requirements.txt /app/
RUN pip install -r requirements.txt

# Копируем код API
COPY src/api/app.py /app/
COPY model.pkl /app/

# Экспонируем порт FastAPI
EXPOSE 8000

# Запуск сервера uvicorn
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
