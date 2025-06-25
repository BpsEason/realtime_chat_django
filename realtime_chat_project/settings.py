"""
Django settings for realtime_chat_project project.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""

import os
from pathlib import Path
from decouple import config # 導入 'python-decouple' 套件，用於管理環境變數

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
# 從環境變數讀取 SECRET_KEY，開發時可設定預設值，但生產環境必須明確設置
SECRET_KEY = config('SECRET_KEY', default='django-insecure-your-very-secret-key-for-development-only') 

# SECURITY WARNING: don't run with debug turned on in production!
# 從環境變數讀取 DEBUG，並轉換為布林值。生產環境務必設置為 False
DEBUG = config('DEBUG', default=True, cast=bool) 

# ALLOWED_HOSTS 應明確列出允許訪問的主機名或 IP。生產環境必須從環境變數讀取
# 例如：ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='127.0.0.1,localhost').split(',')
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='127.0.0.1,localhost').split(',')


# Application definition

INSTALLED_APPS = [
    'daphne', # 確保 daphne 在最前面，用於 ASGI 伺服器
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework', # Django REST Framework
    # 'rest_framework_simplejwt', # 如果使用 JWT 認證，需要安裝並啟用
    'chat', # 你的聊天應用
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'realtime_chat_project.urls'

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
                'django.template.context_processors.messages',
            ],
        },
    },
]

# ASGI 應用程序入口點，供 Daphne 或 Gunicorn 搭配 Uvicorn worker 使用
ASGI_APPLICATION = 'realtime_chat_project.asgi.application'

# Channel Layers 配置 (Channels 的訊息中介層)
# REDIS_URL 必須從環境變數讀取。本地開發可設定預設值。
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer', 
        'CONFIG': {
            # 在 Docker Compose 環境中，直接使用服務名稱 'redis' 作為主機名
            "hosts": [config('REDIS_URL', default='redis://redis:6379')],
            # "password": config('REDIS_PASSWORD', default=None), # 如果 Redis 有密碼
        },
    },
}

# 資料庫配置
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
    # 建議在生產環境使用 PostgreSQL 或 MySQL:
    # 'default': {
    #     'ENGINE': 'django.db.backends.postgresql',
    #     'NAME': config('DB_NAME', 'your_db_name'),
    #     'USER': config('DB_USER', 'your_db_user'),
    #     'PASSWORD': config('DB_PASSWORD', 'your_db_password'),
    #     'HOST': config('DB_HOST', 'localhost'), # 如果資料庫也在 Docker Compose 內，這裡將是其服務名
    #     'PORT': config('DB_PORT', '5432'),
    # }
}


# 密碼驗證器
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# 國際化
LANGUAGE_CODE = 'zh-hant' # 更改為繁體中文
TIME_ZONE = 'Asia/Taipei' # 更改為台北時區
USE_I18N = True
USE_TZ = True


# 靜態文件 (CSS, JavaScript, Images)
STATIC_URL = 'static/'
# 部署時，靜態文件將收集到此目錄
STATIC_ROOT = BASE_DIR / 'staticfiles'


# 預設主鍵類型
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Django REST Framework (DRF) 配置
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated', # 預設需要認證
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication', # Session 認證
        'rest_framework.authentication.BasicAuthentication', # 基本認證
        # 如果使用 djangorestframework-simplejwt，請取消註解以下行
        # 'rest_framework_simplejwt.authentication.JWTAuthentication', 
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer', # 方便開發調試
    ]
}

# Optional: JWT settings if you plan to use djangorestframework-simplejwt
# from datetime import timedelta
# SIMPLE_JWT = {
#     'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
#     'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
#     'ROTATE_REFRESH_TOKENS': True,
#     'BLACKLIST_AFTER_ROTATION': True,
#     'ALGORITHM': 'HS256',
#     'SIGNING_KEY': SECRET_KEY,
#     'VERIFYING_KEY': None,
#     'AUDIENCE': None,
#     'ISSUER': None,
#     'AUTH_HEADER_TYPES': ('Bearer',),
#     'USER_ID_FIELD': 'id',
#     'USER_ID_CLAIM': 'user_id',
#     'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
#     'TOKEN_TYPE_CLAIM': 'token_type',
#     'JTI_CLAIM': 'jti',
#     'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
#     'SLIDING_TOKEN_LIFETIME': timedelta(minutes=5),
#     'SLIDING_TOKEN_REFR_LIFETIME': timedelta(days=1),
# }

