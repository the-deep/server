"""
Django settings for deep project.
"""
import os
import sys
from datetime import timedelta

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.11/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    '=p5!pos4^@$tb1yi@++o5_s)ya@62odvk_mf--#8ozaw0wnc0q')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DJANGO_DEBUG', True)

ALLOWED_HOSTS = [os.environ.get('ALLOWED_HOST', '*')]


# See if we are inside a test environment
TESTING = len(sys.argv) > 1 and sys.argv[1] == 'test'


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'rest_framework',
    'django_filters',
    'crispy_forms',
    'rest_framework_simplejwt',
    'djangorestframework_camel_case',
    'rest_framework_swagger',
    'reversion',
    'channels',

    'redis_store',

    'user_resource',
    'user',
    'user_group',
    'project',
    'geo',
    'lead',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'reversion.middleware.RevisionMiddleware',
]

ROOT_URLCONF = 'deep.urls'

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

WSGI_APPLICATION = 'deep.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.environ.get('DATABASE_NAME', 'postgres'),
        'USER': os.environ.get('DATABASE_USER', 'postgres'),
        'PASSWORD': os.environ.get('DATABASE_USER', 'postgres'),
        'PORT': os.environ.get('DATABASE_PORT', '5432'),
        'HOST': os.environ.get('DATABASE_HOST', 'db'),
    }
}


# Password validation
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.'
        'UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.'
        'MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.'
        'CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.'
        'NumericPasswordValidator',
    },
]

# Authentication
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'EXCEPTION_HANDLER': 'deep.exception_handler.custom_exception_handler',
    'DEFAULT_RENDERER_CLASSES': (
        'djangorestframework_camel_case.render.CamelCaseJSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ),
    'DEFAULT_PARSER_CLASSES': (
        'djangorestframework_camel_case.parser.CamelCaseJSONParser',
        'rest_framework.parsers.FormParser',
    ),
    'DEFAULT_VERSIONING_CLASS':
        'rest_framework.versioning.URLPathVersioning',
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
    ),

    'DEFAULT_PAGINATION_CLASS':
        'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 100,
}

# Crispy forms for better django filters rendering
CRISPY_TEMPLATE_PACK = 'bootstrap3'

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
}

DEFAULT_VERSION = 'v1'

# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


REACT_APP_DIR = os.path.join(BASE_DIR, '../frontend')


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/

STATIC_URL = '/static/'
STATICFILES_DIRS = [
    os.path.join(REACT_APP_DIR, 'build', 'static'),
]

STATIC_ROOT = '/static'

MEDIA_URL = '/media/'
MEDIA_ROOT = '/media'


# CELERY CONFIG

CELERY_BROKER_URL = os.environ.get('REDIS_URL', 'redis://redis:6379')
CELERY_RESULT_BACKEND = os.environ.get('REDIS_URL', 'redis://redis:6379')
CELERY_TIMEZONE = TIME_ZONE

# REDIS STORE CONFIG

REDIS_STORE_HOST = os.environ.get('REDIS_HOST', 'redis')
REDIS_STORE_PORT = os.environ.get('REDIS_PORT', '6379')
REDIS_STORE_DB = os.environ.get('REDIS_DB_NUM', '0')


# CHANNELS CONFIG
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'asgi_redis.RedisChannelLayer',
        'CONFIG': {
            'hosts': [(os.environ.get('REDIS_HOST', 'redis'), 6379)],
        },
        'ROUTING': 'deep.routing.channel_routing',
    },
}

TEST_DIR = os.path.join(BASE_DIR, 'deep/test_files')

# HID CONFIGS [NOTE: Update config in React too]
HID_CLIENT_ID = os.environ.get('HID_CLIENT_ID', 'deep-local')
HID_CLIENT_NAME = os.environ.get('HID_CLIENT_NAME', 'Deep Local')
HID_CLIENT_REDIRECT_URL = os.environ.get(
    'HID_CLIENT_REDIRECT_URL', 'http://localhost:3000/login/')
HID_AUTH_URI = os.environ.get(
    'HID_AUTH_URI',
    'https://api2.dev.humanitarian.id')  # https://api2.dev.humanitarian.id
