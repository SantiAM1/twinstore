#!/bin/sh

echo "Iniciando Celery Beat..."

sleep 5

exec celery -A config beat \
    --loglevel=info \
    --scheduler django_celery_beat.schedulers:DatabaseScheduler

echo "Celery Beat iniciado."