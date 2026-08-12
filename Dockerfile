# Dockerfile для GrafikRaboty
# Multi-stage build для оптимизации размера образа

# Stage 1: Build
FROM python:3.12-slim as builder

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Копирование requirements и установка Python зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt
RUN pip install --no-cache-dir psycopg2-binary gunicorn

# Stage 2: Production
FROM python:3.12-slim

WORKDIR /app

# Метки
LABEL maintainer="Denis <@denisvetgid>"
LABEL version="4.30"
LABEL description="GrafikRaboty Server - Schedule & Task Management"

# Создание пользователя для безопасности
RUN useradd --create-home --shell /bin/bash appuser

# Копирование установленных пакетов из builder
COPY --from=builder /root/.local /home/appuser/.local

# Копирование исходного кода
COPY . .

# Создание необходимых директорий
RUN mkdir -p /app/data /app/uploads /app/logs /app/instance && \
    chown -R appuser:appuser /app

# Переключение на не-root пользователя
USER appuser

# Добавление локальных пакетов в PATH
ENV PATH=/home/appuser/.local/bin:$PATH

# Переменные окружения по умолчанию
ENV FLASK_ENV=production
ENV PORT=8080

# Экспонирование порта
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/api/health', timeout=5)" || exit 1

# Запуск приложения через Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "4", "--threads", "2", \
     "--worker-class", "gevent", "--timeout", "120", \
     "--access-logfile", "-", "--error-logfile", "-", \
     "--capture-output", "web_server:app"]
