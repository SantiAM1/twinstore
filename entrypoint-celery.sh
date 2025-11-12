#!/bin/sh

echo "Iniciando Celery Worker..."
sleep 5

mkdir -p /app/logs && chmod 777 /app/logs || true
touch /app/logs/mercadopago.log && chmod 666 /app/logs/mercadopago.log || true

exec celery -A config worker \
    --loglevel=info \
    --concurrency=2 \
    --prefetch-multiplier=1 \
    --max-tasks-per-child=100

echo "Celery Worker iniciado."