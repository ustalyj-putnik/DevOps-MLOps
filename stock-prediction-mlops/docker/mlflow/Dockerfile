FROM python:3.10-slim

# Устанавливаем MLflow и boto3
RUN pip install mlflow boto3

# Переменные окружения для AWS/S3
ENV AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID
ENV AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY

# Экспонируем порт MLflow
EXPOSE 5000

# Запуск MLflow-сервера с SQLite в качестве хранилища метаданных и S3 для артефактов
CMD mlflow server \
    --host 0.0.0.0 \
    --port 5000 \
    --backend-store-uri sqlite:///mlflow.db \
    --default-artifact-root s3://$S3_BUCKET/mlflow
