#!/bin/bash
set -e

# Проверка переменных окружения
echo "Checking environment variables..."
if [ -z "$DB_HOST" ] || [ -z "$DB_PORT" ] || [ -z "$POSTGRES_USER" ] || [ -z "$POSTGRES_DB" ]; then
    echo "Error: Missing required database environment variables"
    exit 1
fi

echo "Waiting for PostgreSQL at $DB_HOST:$DB_PORT..."
for i in {1..30}; do
    if PGPASSWORD=$POSTGRES_PASSWORD psql -h "$DB_HOST" -p "$DB_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT 1;" >/dev/null 2>&1; then
        echo "PostgreSQL is ready!"
        break
    fi
    echo "Attempt $i: PostgreSQL not ready yet..."
    sleep 2
done

# Проверка окончательного подключения
if ! PGPASSWORD=$POSTGRES_PASSWORD psql -h "$DB_HOST" -p "$DB_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT 1;" >/dev/null 2>&1; then
    echo "Error: Failed to connect to PostgreSQL after 30 attempts"
    exit 1
fi

# Применение миграций
echo "Applying database migrations..."
python manage.py migrate --noinput

# Сбор статики
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

# Создание суперпользователя (только при первом запуске)
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