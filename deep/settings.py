"""
Django settings for deep project.
"""
import os
import sys

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.11/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    '=p5!pos4^@$tb1yi@++o5_s)ya@62odvk_mf--#8ozaw0wnc0q')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DJANGO_DEBUG', 'True').lower() == 'true'

ALLOWED_HOSTS = [os.environ.get('DJANGO_ALLOWED_HOST', '*')]


# See if we are inside a test environment
TESTING = len(sys.argv) > 1 and sys.argv[1] == 'test'


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.messages',
    'django.contrib.sessions',
    'django.contrib.staticfiles',

    'channels',
    'channels',
    'corsheaders',
    'crispy_forms',
    'django_filters',
    'djangorestframework_camel_case',
    'drf_dynamic_fields',
    'reversion',

    'redis_store',
    'rest_framework',
    'reversion',
    'storages',

    'analysis_framework',
    'docs',
    'dummy_data',
    'entry',
    'gallery',
    'geo',
    'lead',
    'project',
    'user',
    'user_group',
    'user_resource',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
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
        'PASSWORD': os.environ.get('DATABASE_PASSWORD', 'postgres'),
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
        'jwt_auth.authentication.JwtAuthentication',
    ),
    'EXCEPTION_HANDLER': 'deep.exception_handler.custom_exception_handler',
    'DEFAULT_RENDERER_CLASSES': (
        'djangorestframework_camel_case.render.CamelCaseJSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ),
    'DEFAULT_PARSER_CLASSES': (
        'djangorestframework_camel_case.parser.CamelCaseJSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
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

DEFAULT_VERSION = 'v1'

# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/

if os.environ.get('DJANGO_USE_S3', 'False').lower() == 'true':
    # AWS S3 Bucket Credentials
    AWS_STORAGE_BUCKET_NAME_STATIC = os.environ[
        'DJANGO_AWS_STORAGE_BUCKET_NAME_STATIC']
    AWS_STORAGE_BUCKET_NAME_MEDIA = os.environ[
        'DJANGO_AWS_STORAGE_BUCKET_NAME_MEDIA']
    AWS_ACCESS_KEY_ID = os.environ['S3_AWS_ACCESS_KEY_ID']
    AWS_SECRET_ACCESS_KEY = os.environ['S3_AWS_SECRET_ACCESS_KEY']

    AWS_S3_FILE_OVERWRITE = False
    AWS_DEFAULT_ACL = 'private'
    AWS_QUERYSTRING_AUTH = True
    AWS_S3_CUSTOM_DOMAIN = None

    # Static configuration
    STATICFILES_LOCATION = 'static'
    STATIC_URL = "https://%s/%s/" % (AWS_S3_CUSTOM_DOMAIN,
                                     STATICFILES_LOCATION)
    STATICFILES_STORAGE = 'deep.s3_storages.StaticStorage'

    # Media configuration
    MEDIAFILES_LOCATION = 'media'
    MEDIA_URL = "https://%s/%s/" % (AWS_S3_CUSTOM_DOMAIN, MEDIAFILES_LOCATION)
    DEFAULT_FILE_STORAGE = 'deep.s3_storages.MediaStorage'
else:
    STATIC_URL = '/static/'
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
    'https://api2.dev.humanitarian.id')  # https://auth.humanitarian.id

# Logging Errors to Papertrail


def add_username_attribute(record):
    """
    Append username(email) to logs
    """
    if hasattr(record, 'request'):
        if hasattr(record.request, 'user') and\
                not record.request.user.is_anonymous():
            record.username = record.request.user.username
        else:
            record.username = 'Anonymous_User'
    return True


if os.environ.get('USE_PAPERTRAIL', 'False').lower() == 'true':
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'filters': {
            'add_username_attribute': {
                '()': 'django.utils.log.CallbackFilter',
                'callback': add_username_attribute,
            }
        },
        'formatters': {
            'simple': {
                'format': '%(asctime)s ' + os.environ.get('EBS_HOSTNAME', '') +
                          ' DJANGO-' + os.environ.get('EBS_ENV_TYPE', '') +
                          ': %(username)s %(message)s',
                'datefmt': '%Y-%m-%dT%H:%M:%S',
            },
        },
        'handlers': {
            'SysLog': {
                'level': 'DEBUG',
                'class': 'logging.handlers.SysLogHandler',
                'filters': ['add_username_attribute'],
                'formatter': 'simple',
                'address': (os.environ.get('PAPERTRAIL_HOST'),
                            int(os.environ.get('PAPERTRAIL_PORT')))
            },
        },
        'loggers': {
            'celery': {
                'handlers': ['SysLog'],
                'propagate': True,
            },
            'channels': {
                'handlers': ['SysLog'],
                'propagate': True,
            },
            'django': {
                'handlers': ['SysLog'],
                'propagate': True,
            },
        },
    }

# CORS CONFIGS
CORS_ORIGIN_WHITELIST = (
    os.environ.get('FRONTEND_HOST', 'localhost:3000')
)

CORS_URLS_REGEX = r'^/api/.*$'

CORS_ALLOW_METHODS = (
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
)

CORS_ALLOW_HEADERS = (
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
)

# Email CONFIGS
USE_EMAIL_CONFIG = os.environ.get('USE_EMAIL_CONFIG',
                                  'False').lower() == 'true'
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER',
                                 'deepnotifications1@gmail.com')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', 'deep1234')
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True').lower() == 'true'
EMAIL_PORT = int(os.environ.get('EMAIL_PORT')) if os.environ.get('EMAIL_PORT')\
    else 587
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
ADMINS = [('Ewan', 'ewanogle@gmail.com'),
          ('Togglecorp', 'info@togglecorp.com')]

if not USE_EMAIL_CONFIG:
    """
    DUMP THE EMAIL TO CONSOLE
    """
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
