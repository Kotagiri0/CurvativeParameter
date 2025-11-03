#!/bin/bash
set -e

echo "=========================================="
echo "Starting Django application on Render"
echo "=========================================="

# Проверка DATABASE_URL
if [ -z "$DATABASE_URL" ]; then
    echo "❌ ERROR: DATABASE_URL is not set!"
    exit 1
fi

echo "✓ DATABASE_URL is configured"

# Функция ожидания PostgreSQL
wait_for_db() {
    echo ""
    echo "Waiting for PostgreSQL to be ready..."

    max_attempts=60
    attempt=0

    while [ $attempt -lt $max_attempts ]; do
        attempt=$((attempt + 1))

        # Пытаемся подключиться через Django
        if python << END
import sys
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'website.settings')

try:
    import django
    django.setup()
    from django.db import connection
    connection.ensure_connection()
    print("✓ Database connection successful!")
    sys.exit(0)
except Exception as e:
    print(f"Attempt {attempt}: Connection failed - {str(e)[:100]}")
    sys.exit(1)
END
        then
            echo "✓ PostgreSQL is ready!"
            return 0
        fi

        sleep 2
    done

    echo "❌ PostgreSQL is not ready after ${max_attempts} attempts (120 seconds)!"
    echo "Please check:"
    echo "  1. PostgreSQL service is running on Render"
    echo "  2. DATABASE_URL is correct"
    echo "  3. Network connectivity between services"
    exit 1
}

# Ждём базу данных
wait_for_db

echo ""
echo "=========================================="
echo "Running Django management commands"
echo "=========================================="

# Применение миграций
echo ""
echo "→ Applying database migrations..."
python manage.py migrate --noinput || {
    echo "❌ Migration failed!"
    exit 1
}
echo "✓ Migrations applied successfully"

# Сбор статики
echo ""
echo "→ Collecting static files..."
python manage.py collectstatic --noinput --clear || {
    echo "❌ Static collection failed!"
    exit 1
}
echo "✓ Static files collected"

# Создание суперпользователя (если переменные заданы)
if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_EMAIL" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
    echo ""
    echo "→ Creating superuser..."
    python manage.py createsuperuser \
        --noinput \
        --username "$DJANGO_SUPERUSER_USERNAME" \
        --email "$DJANGO_SUPERUSER_EMAIL" 2>&1 | grep -v "That username is already taken" || true
    echo "✓ Superuser check complete"
fi

echo ""
echo "=========================================="
echo "Starting Gunicorn server"
echo "=========================================="
echo "Workers: 4 | Threads: 2 | Timeout: 120s"
echo ""

# Запуск Gunicorn
exec gunicorn website.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --threads 2 \
    --timeout 120 \
    --worker-class gthread \
    --access-logfile - \
    --error-logfile - \
    --log-level info