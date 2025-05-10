# Stage 1: builder с зависимостями
FROM python:3.10 AS builder
WORKDIR /app
COPY requirements.txt /app/
RUN pip install --user -r requirements.txt

# Stage 2: финальный образ
FROM python:3.10-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

COPY . /app
# Скрипт обучения вызывается по умолчанию
CMD ["bash", "scripts/train.sh"]
