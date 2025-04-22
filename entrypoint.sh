#!/bin/bash
set -e

# Ожидание MySQL с таймаутом
echo "Waiting for MySQL..."
timeout 60 bash -c 'until mysqladmin ping -h mysql -u myuser -p$$MYSQL_PASSWORD --silent; do sleep 2; done'
echo "MySQL is ready!"

# Применение миграций
python manage.py migrate --no-input

# Сбор статики
python manage.py collectstatic --no-input --clear

# Создание суперпользователя
if [ "$DJANGO_SUPERUSER_USERNAME" ]; then
  python manage.py createsuperuser \
    --noinput \
    --username $DJANGO_SUPERUSER_USERNAME \
    --email $DJANGO_SUPERUSER_EMAIL || true
fi

# Запуск сервера
exec gunicorn --bind 0.0.0.0:8000 website.wsgi:application