import os
from pathlib import Path
from dotenv import load_dotenv

# ===== Загружаем переменные окружения =====
load_dotenv()

# ===== Базовые пути =====
BASE_DIR = Path(__file__).resolve().parent.parent
LOGIN_URL = 'login'

# ===== Cloudinary URL должен быть в .env =====
# Пример строки в .env:
# CLOUDINARY_URL=cloudinary://<api_key>:<api_secret>@<cloud_name>
CLOUDINARY_URL = os.getenv('CLOUDINARY_URL')
if not CLOUDINARY_URL:
    raise RuntimeError("❌ Переменная CLOUDINARY_URL не найдена в .env — добавь её!")

# ===== Хранилище файлов через Cloudinary =====
DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
MEDIA_URL = ''  # можно и без жёсткой привязки, но тогда нужна логика
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')  # просто чтобы static() не падал



# ===== Безопасность =====
SECRET_KEY = os.getenv('SECRET_KEY', 'fallback-key')
DEBUG = os.getenv('DEBUG', '1') == '1'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',') if not DEBUG else ['*']

# ===== Приложения =====
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'main',

    # Cloudinary
    'cloudinary',
    'cloudinary_storage',
]

# ===== Middleware =====
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'website.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'website.wsgi.application'

# ===== База данных =====
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ===== Валидация паролей =====
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ===== Локализация =====
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# ===== Статика =====
STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# ===== Автоматическое поле =====
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ===== Отладочная печать =====
print("Cloudinary URL from env:", CLOUDINARY_URL)
from django.core.files.storage import default_storage
print("Default storage backend:", default_storage)
