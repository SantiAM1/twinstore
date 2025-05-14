#!/bin/sh

echo "Iniciando Celery Worker..."
celery -A config worker --loglevel=info --concurrency=1