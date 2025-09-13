"""
Django settings for website project.
"""

import os
from pathlib import Path

# ===== Базовые пути =====
BASE_DIR = Path(__file__).resolve().parent.parent

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

    # Social Auth
    'social_django',
]

# ===== Аутентификация =====
AUTHENTICATION_BACKENDS = [
    'social_core.backends.google.GoogleOAuth2',   # ✅ Google OAuth2
    'django.contrib.auth.backends.ModelBackend',  # стандартный бэкенд
]

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = '/'      # куда отправлять после логина
LOGOUT_REDIRECT_URL = '/'     # куда после выхода

# ===== Google OAuth2 =====
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = os.getenv('GOOGLE_CLIENT_ID')         # client_id
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')  # client_secret

# ===== Middleware =====
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    # Social Auth
    'social_django.middleware.SocialAuthExceptionMiddleware',
]

ROOT_URLCONF = 'website.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # можно хранить шаблоны здесь
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',

                # Social Auth
                'social_django.context_processors.backends',
                'social_django.context_processors.login_redirect',
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

# ===== Cloudinary =====
env_path = BASE_DIR / '.env'
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ.setdefault(key, value)

CLOUDINARY_URL = os.getenv('CLOUDINARY_URL')
if not CLOUDINARY_URL:
    raise RuntimeError("❌ CLOUDINARY_URL не найдена!")

DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
MEDIA_URL = ''
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

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
