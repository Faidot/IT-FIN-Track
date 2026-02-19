FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# system deps for building some Python packages (psycopg2, Pillow)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       libpq-dev \
       gcc \
       libjpeg-dev \
       zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

# Collect static files at build time (harmless if STATIC_ROOT is writable)
RUN python manage.py collectstatic --noinput || true

EXPOSE 8000

CMD ["gunicorn", "itfintrack.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
