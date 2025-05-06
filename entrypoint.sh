#!/bin/sh

echo "Aplicando migraciones..."
python manage.py migrate --noinput

echo "Recolectando archivos estáticos..."
python manage.py collectstatic --noinput

echo "Comprimir archivos con django-compressor..."
python manage.py compress --force

echo "Iniciando servidor Gunicorn..."
exec gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers=2 --timeout=30