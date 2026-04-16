FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libmagic1 \
    libpangocairo-1.0-0 \
    libcairo2 \
    pango1.0-tools \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    shared-mime-info \
    && apt-get clean

# EntryPoints
COPY entrypoint.sh /entrypoint.sh
COPY entrypoint-celery.sh /entrypoint-celery.sh
COPY entrypoint-beat.sh /entrypoint-beat.sh

RUN chmod +x /entrypoint.sh /entrypoint-celery.sh /entrypoint-beat.sh
# * Copiar requirements e instalarlos
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

EXPOSE 8000
ENTRYPOINT ["/entrypoint.sh"]