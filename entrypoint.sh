#!/bin/bash
set -e

echo "Using DATABASE_URL, skipping direct postgres env checks"

# Применение миграций
echo "Applying database migrations..."
python manage.py migrate --noinput

# Сбор статики
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

# Создание суперпользователя (если переменные заданы)
if [ "$DJANGO_SUPERUSER_USERNAME" ] && [ "$DJANGO_SUPERUSER_EMAIL" ] && [ "$DJANGO_SUPERUSER_PASSWORD" ]; then
    echo "Creating superuser..."
    python manage.py createsuperuser \
        --noinput \
        --username "$DJANGO_SUPERUSER_USERNAME" \
        --email "$DJANGO_SUPERUSER_EMAIL" || \
        echo "Superuser creation skipped (already exists or failed)"
fi

# Запуск Gunicorn
echo "Starting Gunicorn..."
exec gunicorn website.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --threads 2 \
    --timeout 120 \
    --worker-class gthread
