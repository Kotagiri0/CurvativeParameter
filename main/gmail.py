import re
import smtplib
import dns.resolver
from django.contrib import messages
from django.shortcuts import redirect
from .models import User


def check_gmail_exists(email):
    """Проверка существования Gmail аккаунта через SMTP."""
    try:
        # Извлекаем домен из email
        domain = email.split('@')[1]

        # Проверяем MX-записи домена
        mx_records = dns.resolver.resolve(domain, 'MX')
        mx_host = mx_records[0].exchange.to_text()

        # Устанавливаем соединение с SMTP-сервером
        server = smtplib.SMTP()
        server.set_debuglevel(0)
        server.connect(mx_host)
        server.helo(server.local_hostname)
        server.mail('test@yourdomain.com')  # Отправитель (замените на ваш домен)
        code, _ = server.rcpt(email)  # Проверяем получателя
        server.quit()

        # Код 250 обычно означает, что email существует
        return code == 250
    except Exception as e:
        # Если произошла ошибка (например, сервер блокирует), считаем email неподтвержденным
        return False


def validate_gmail(request, user, email):
    if not email:
        messages.error(request, 'Email не может быть пустым.')
        return redirect('profile')

    # Проверка формата email для Gmail
    gmail_pattern = r'^[a-zA-Z0-9._%+-]+@gmail\.com$'
    if not re.match(gmail_pattern, email):
        messages.error(request, 'Пожалуйста, используйте действительный Gmail адрес.')
        return redirect('profile')

    # Проверка уникальности email
    if User.objects.exclude(pk=user.pk).filter(email__iexact=email).exists():
        messages.error(request, 'Этот Gmail адрес уже используется.')
        return redirect('profile')

    # Проверка существования Gmail аккаунта
    if not check_gmail_exists(email):
        messages.error(request, 'Этот Gmail адрес не существует.')
        return redirect('profile')

    return None  # Возвращает None, если валидация прошла успешно