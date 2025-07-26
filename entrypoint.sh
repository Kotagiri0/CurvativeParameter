#!/bin/bash
set -e

echo "Environment variables:"
echo "DB_HOST=$DB_HOST DB_PORT=$DB_PORT DB_USER=$DB_USER DB_NAME=$DB_NAME"

echo "Waiting for PostgreSQL..."
for i in {1..30}; do
    if pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER"; then
        echo "PostgreSQL is ready!"
        break
    fi
    echo "Attempt $i: PostgreSQL not ready yet..."
    sleep 2
done

if ! pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER"; then
    echo "Error: PostgreSQL is not ready after 60 seconds!"
    exit 1
fi

# Создание миграций
echo "Creating migrations..."
python manage.py makemigrations

# Применение миграций
echo "Running migrations..."
python manage.py migrate --no-input

# Сбор статики
echo "Collecting static files..."
python manage.py collectstatic --no-input --clear

# Создание суперпользователя
echo "Creating superuser..."
export DJANGO_SETTINGS_MODULE=website.settings
python manage.py createsuperuser --noinput --username "$DJANGO_SUPERUSER_USERNAME" --email "$DJANGO_SUPERUSER_EMAIL" || echo "Superuser already exists or failed to create."

# Запуск Gunicorn
echo "Starting Gunicorn..."
exec gunicorn website.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --threads 4 \
    --timeout 600 \
    --worker-class gthread