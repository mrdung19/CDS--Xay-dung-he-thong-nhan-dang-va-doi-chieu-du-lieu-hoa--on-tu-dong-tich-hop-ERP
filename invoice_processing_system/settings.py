# invoice_processing_system/settings.py

import os
import sys
from pathlib import Path

# ------------------------------------------------
# Cấu hình Cơ bản (BASE_DIR)
# ------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent 

# ------------------------------------------------
# FIX LỖI THREAD TRIỆT ĐỂ - THÊM ĐOẠN NÀY ĐẦU TIÊN
# ------------------------------------------------
import sqlite3
from sqlite3 import connect as sqlite_connect

# Monkey patch để fix lỗi thread SQLite
def sqlite3_connect(*args, **kwargs):
    kwargs['check_same_thread'] = False
    return sqlite_connect(*args, **kwargs)

sqlite3.connect = sqlite3_connect

# Vô hiệu hóa kiểm tra thread sharing
from django.db.backends.base.base import BaseDatabaseWrapper
BaseDatabaseWrapper.validate_thread_sharing = lambda self: None

# ------------------------------------------------
# Cài đặt Bảo mật
# ------------------------------------------------
SECRET_KEY = 'django-insecure-your-secret-key-here' 
DEBUG = True 
ALLOWED_HOSTS = ['127.0.0.1', 'localhost', '[::1]']

# ------------------------------------------------
# Cấu hình Ứng dụng
# ------------------------------------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'invoice_processing_system.app_invoices',

]

# Cấu hình Middleware theo đúng thứ tự
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware', 
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'invoice_processing_system.urls'

# Cấu hình TEMPLATES
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates', 
        'DIRS': [BASE_DIR / 'templates'], 
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

WSGI_APPLICATION = 'invoice_processing_system.wsgi.application'

# ------------------------------------------------
# Cấu hình Database - ĐÃ SỬA TRIỆT ĐỂ
# ------------------------------------------------
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3', 
        'NAME': BASE_DIR / 'db.sqlite3',
        'OPTIONS': {
            'timeout': 30,
            'check_same_thread': False,  # QUAN TRỌNG
        }
    }
}

# Tắt connection pooling
DATABASE_CONNECTION_POOLING = False

# ------------------------------------------------
# Các cấu hình khác
# ------------------------------------------------
LOGIN_URL = '/invoices/login/'
LOGIN_REDIRECT_URL = '/invoices/'  

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',},
]

LANGUAGE_CODE = 'vi'
TIME_ZONE = 'Asia/Ho_Chi_Minh'
USE_I18N = True
USE_TZ = True

# ------------------------------------------------
# Cấu hình Static Files 
# ------------------------------------------------
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'static', 
]
STATIC_ROOT = BASE_DIR / 'staticfiles'

# ------------------------------------------------
# Cấu hình Media Files
# ------------------------------------------------
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ------------------------------------------------
# Cấu hình OCR & AI
# ------------------------------------------------
TESSERACT_CMD = r"C:\Program Files\Tesseract-OCR\tesseract.exe" 
GOOGLE_VISION_CREDENTIALS = os.path.join(BASE_DIR, 'config', 'google_cloud_key.json') 

# Đặt biến môi trường Google Cloud
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = GOOGLE_VISION_CREDENTIALS

# ------------------------------------------------
# Cấu hình CELERY
# ------------------------------------------------
CELERY_BROKER_URL = 'redis://localhost:6379/0' 
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Asia/Ho_Chi_Minh'

# ------------------------------------------------
# Cấu hình Django REST Framework
# ------------------------------------------------
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated', 
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication', 
    ],
    'EXCEPTION_HANDLER': 'rest_framework.views.exception_handler',
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ]
}

# ------------------------------------------------
# THÊM CẤU HÌNH ĐỂ TRÁNH CẢNH BÁO STATIC FILES
# ------------------------------------------------
# Bỏ qua cảnh báo static files nếu thư mục không tồn tại
SILENCED_SYSTEM_CHECKS = ['staticfiles.W004']