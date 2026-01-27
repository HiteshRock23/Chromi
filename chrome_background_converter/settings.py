# from pathlib import Path
# import os
# from decouple import config, Csv

# BASE_DIR = Path(__file__).resolve().parent.parent

# # SECURITY WARNING: keep the secret key used in production secret!
# SECRET_KEY = config('SECRET_KEY')

# # SECURITY WARNING: don't run with debug turned on in production!
# # DEBUG = config('DEBUG', default=False, cast=bool)
# DEBUG = config('DEBUG', default=True, cast=bool)

# ALLOWED_HOSTS = config(
#     'ALLOWED_HOSTS',
#     default='localhost,127.0.0.1',
#     cast=Csv()
# )
# # ALLOWED_HOSTS = ['*']

# # When developing locally you can enable HTTPS by setting USE_HTTPS=True in your
# # environment (.env). This will enable SSL redirects and secure cookies while
# # DEBUG is still True so you can test HTTPS locally (you still need to run a
# # devserver that serves TLS, see README / instructions below).
# USE_HTTPS = config('USE_HTTPS', default=False, cast=bool)

# # Security settings for production and optional local HTTPS
# # If the application runs behind a proxy (nginx, Cloud Run, etc.) make sure
# # the proxy sets X-Forwarded-Proto header — we respect it below.
# SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# if DEBUG:
#     # Local development. Allow enabling HTTPS behavior via USE_HTTPS env var
#     # so developers can test HTTPS-only behaviours without switching to the
#     # full production branch. Note: enabling USE_HTTPS requires running a
#     # development server that serves TLS (see run instructions).
#     SECURE_SSL_REDIRECT = USE_HTTPS
#     # Only enable HSTS in debug if USE_HTTPS is True; otherwise keep it off.
#     SECURE_HSTS_SECONDS = 31536000 if USE_HTTPS else 0
#     SECURE_HSTS_INCLUDE_SUBDOMAINS = bool(USE_HTTPS)
#     SECURE_HSTS_PRELOAD = bool(USE_HTTPS)
# else:
#     # Production security - always on
#     SECURE_SSL_REDIRECT = True
#     SECURE_HSTS_SECONDS = 31536000  # 1 year
#     SECURE_HSTS_INCLUDE_SUBDOMAINS = True
#     SECURE_HSTS_PRELOAD = True
#     SECURE_BROWSER_XSS_FILTER = True
#     SECURE_CONTENT_TYPE_NOSNIFF = True
#     X_FRAME_OPTIONS = 'DENY'

# # Secure cookies: enable when serving HTTPS (either in production or locally
# # when USE_HTTPS=True). This ensures session and CSRF cookies are only sent
# # over secure channels.
# SESSION_COOKIE_SECURE = (not DEBUG) or USE_HTTPS
# CSRF_COOKIE_SECURE = (not DEBUG) or USE_HTTPS

# # Application definition
# INSTALLED_APPS = [
#     'django.contrib.admin',
#     'django.contrib.auth',
#     'django.contrib.contenttypes',
#     'django.contrib.sessions',
#     'django.contrib.messages',
#     'django.contrib.staticfiles',
#     'converter',
# ]

# MIDDLEWARE = [
#     'django.middleware.security.SecurityMiddleware',
#     'whitenoise.middleware.WhiteNoiseMiddleware',
#     'django.contrib.sessions.middleware.SessionMiddleware',
#     'django.middleware.common.CommonMiddleware',
#     'django.middleware.csrf.CsrfViewMiddleware',
#     'django.contrib.auth.middleware.AuthenticationMiddleware',
#     'django.contrib.messages.middleware.MessageMiddleware',
#     'django.middleware.clickjacking.XFrameOptionsMiddleware',
# ]

# ROOT_URLCONF = 'chrome_background_converter.urls'

# TEMPLATES = [
#     {
#         'BACKEND': 'django.template.backends.django.DjangoTemplates',
#         'DIRS': [BASE_DIR / 'templates'],
#         'APP_DIRS': True,
#         'OPTIONS': {
#             'context_processors': [
#                 'django.template.context_processors.request',
#                 'django.contrib.auth.context_processors.auth',
#                 'django.contrib.messages.context_processors.messages',
#                 'django.template.context_processors.media',
#             ],
#         },
#     },
# ]

# WSGI_APPLICATION = 'chrome_background_converter.wsgi.application'

# # Database
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }

# # Password validation
# AUTH_PASSWORD_VALIDATORS = [
#     {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
#     {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
#     {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
#     {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
# ]

# # Internationalization
# LANGUAGE_CODE = 'en-us'
# TIME_ZONE = 'UTC'
# USE_I18N = True
# USE_TZ = True

# # Static files
# STATIC_URL = '/static/'
# STATIC_ROOT = BASE_DIR / 'staticfiles'
# STATICFILES_DIRS = [BASE_DIR / 'static']
# STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# # Media files
# MEDIA_URL = '/media/'
# MEDIA_ROOT = BASE_DIR / 'media'

# # File upload size limit (100MB)
# FILE_UPLOAD_MAX_MEMORY_SIZE = 104857600

# # Default primary key field type
# DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# # Logging
# LOGGING = {
#     'version': 1,
#     'disable_existing_loggers': False,
#     'handlers': {
#         'console': {'class': 'logging.StreamHandler'},
#     },
#     'root': {
#         'handlers': ['console'],
#         'level': 'INFO',
#     },
# }

# # Background jobs and memory diagnostics
# USE_RQ = config('USE_RQ', default=False, cast=bool)
# REDIS_URL = config('REDIS_URL', default='redis://localhost:6379/0')
# ENABLE_TRACEMALLOC = config('ENABLE_TRACEMALLOC', default=False, cast=bool)


from pathlib import Path
import os
from decouple import config, Csv

BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='your-local-secret-key')

# Local Development Mode
DEBUG = True
USE_HTTPS = False
ALLOWED_HOSTS = ['*']

# Do not force HTTPS locally
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False

# Cookies should work fine without HTTPS
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Comment out proxy header since we’re not behind Nginx locally
# SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'converter',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # WhiteNoise is optional; you can keep it for serving static files
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'chrome_background_converter.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',
            ],
        },
    },
]

WSGI_APPLICATION = 'chrome_background_converter.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
# Use default static file storage (not compressed) for local dev
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# File upload size limit (100MB)
FILE_UPLOAD_MAX_MEMORY_SIZE = 104857600

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {'class': 'logging.StreamHandler'},
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}

# Background jobs and memory diagnostics (optional)
USE_RQ = config('USE_RQ', default=False, cast=bool)
REDIS_URL = config('REDIS_URL', default='redis://localhost:6379/0')
ENABLE_TRACEMALLOC = config('ENABLE_TRACEMALLOC', default=False, cast=bool)
