#!/bin/sh

echo "Aplicando migraciones..."
python manage.py migrate --noinput

echo "Recolectando archivos estáticos..."
python manage.py collectstatic --noinput

echo "Iniciando servidor Gunicorn..."
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers=3 \
    --threads=2 \
    --timeout=60 \
    --max-requests=500 \
    --max-requests-jitter=50