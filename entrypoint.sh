#!/bin/sh
set -e

# Ожидаем готовности MySQL
echo "Waiting for MySQL..."
while ! mysqladmin ping -h mysql --silent; do
    sleep 1
done
echo "MySQL is up!"

# Выполняем миграции
python manage.py migrate

# Создаем суперпользователя, если он не существует
python manage.py shell <<EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin')
    print('Superuser created.')
else:
    print('Superuser already exists.')
EOF

# Запускаем сервер
exec python manage.py runserver 0.0.0.0:8000