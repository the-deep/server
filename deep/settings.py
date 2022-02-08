"""
Django settings for deep project.
"""
import os
import sys
import logging
import json
import environ
from celery.schedules import crontab
from email.utils import parseaddr

from utils import sentry
from utils.aws import fetch_db_credentials_from_secret_arn, get_internal_ip as get_aws_internal_ip


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APPS_DIR = os.path.join(BASE_DIR, 'apps')
TEMP_DIR = '/tmp'

# TODO: Make sure to pull as much from env then default values.
env = environ.Env(
    DJANGO_DEBUG=(bool, False),
    DJANGO_SECRET_KEY=str,
    DEEP_ENVIRONMENT=(str, 'development'),
    SERVICE_ENVIRONMENT_TYPE=str,
    DEEP_FRONTEND_ARY_HOST=str,
    DEEP_FRONTEND_HOST=str,
    DEEP_BACKEND_HOST=str,
    DJANGO_ALLOWED_HOST=str,
    DEEPER_SITE_NAME=(str, 'DEEPER'),
    # Database
    DATABASE_NAME=str,
    DATABASE_USER=str,
    DATABASE_PASSWORD=str,
    DATABASE_PORT=str,
    DATABASE_HOST=str,
    # S3
    DJANGO_USE_S3=(bool, False),
    S3_AWS_ACCESS_KEY_ID=(str, None),
    S3_AWS_SECRET_ACCESS_KEY=(str, None),
    S3_AWS_ENDPOINT_URL=(str, None),
    CELERY_REDIS_URL=str,
    DJANGO_CACHE_REDIS_URL=str,
    # HID
    HID_CLIENT_ID=str,
    HID_CLIENT_REDIRECT_URL=str,
    HID_AUTH_URI=str,
    # Email
    EMAIL_FROM=str,
    DJANGO_ADMINS=(str, 'admin@thedeep.io'),
    USE_SES_EMAIL_CONFIG=(bool, False),
    SES_AWS_ACCESS_KEY_ID=(str, None),
    SES_AWS_SECRET_ACCESS_KEY=(str, None),
    # Hcaptcha
    HCAPTCHA_SECRET=(str, '0x0000000000000000000000000000000000000000'),
    # Sentry
    SENTRY_DSN=(str, None),
    SENTRY_SAMPLE_RATE=(float, 0.2),
    # Deepl (not used)
    DEEPL_DOMAIN=(str, 'http://192.168.31.92:8010'),
    # Security settings
    DEEP_HTTPS=(str, 'http'),
    # CSRF_TRUSTED_ORIGINS=(bool, False),
    SESSION_COOKIE_DOMAIN=str,
    CSRF_COOKIE_DOMAIN=str,
    DOCKER_HOST_IP=(str, None),
    # DEEPL
    DEEPL_EXTRACTOR_URL=str,  # http://extractor:8001/extract_docs
    DEEPL_EXTRACTOR_CALLBACK_URL=str,  # http://web:8000/api/v1/leads/extract-callback/
    # Pytest
    PYTEST_XDIST_WORKER=(str, None),
    PROFILE=(bool, False),
    # Copilot ENVS
    COPILOT_APPLICATION_NAME=(str, None),
    COPILOT_ENVIRONMENT_NAME=(str, None),
    COPILOT_SERVICE_NAME=(str, None),
    DEEP_DATABASE_SECRET=(json, None),
    DEEP_DATABASE_SECRET_ARN=(str, None),
    DEEP_BUCKET_ACCESS_USER_SECRET=(json, None),
    ELASTI_CACHE_ADDRESS=str,
    ELASTI_CACHE_PORT=str,
)

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.11/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('DJANGO_SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env('DJANGO_DEBUG')

DEEP_ENVIRONMENT = env('COPILOT_ENVIRONMENT_NAME') or env('DEEP_ENVIRONMENT')

ALLOWED_HOSTS = ['web', env('DJANGO_ALLOWED_HOST')]

DEEPER_FRONTEND_HOST = env('DEEP_FRONTEND_HOST')
DEEPER_FRONTEND_ARY_HOST = env('DEEP_FRONTEND_ARY_HOST')  # TODO: Remove this later
DJANGO_API_HOST = env('DEEP_BACKEND_HOST')

DEEPER_SITE_NAME = env('DEEPER_SITE_NAME')
HTTP_PROTOCOL = env('DEEP_HTTPS')

# See if we are inside a test environment (pytest)
TESTING = any([
    arg in sys.argv for arg in [
        'test',
        'pytest', '/usr/local/bin/pytest',
        'py.test', '/usr/local/bin/py.test',
        '/usr/local/lib/python3.6/dist-packages/py/test.py',
    ]
    # Provided by pytest-xdist
]) or env('PYTEST_XDIST_WORKER') is not None
TEST_RUNNER = 'snapshottest.django.TestRunner'
TEST_DIR = os.path.join(BASE_DIR, 'deep/test_files')

PROFILE = env('PROFILE')

# Application definition

LOCAL_APPS = [
    # DEEP APPS
    'analysis',
    'analysis_framework',
    'ary',
    'category_editor',
    'connector',
    'deep_migration',
    'entry',
    'export',
    'gallery',
    'geo',
    'lang',
    'lead',
    'organization',
    'project',
    'user',
    'user_group',
    'user_resource',
    'tabular',
    'notification',
    'client_page_meta',
    'questionnaire',
    'quality_assurance',

    # MISC DEEP APPS
    'bulk_data_migration',
    'profiling',
    'commons',
    'redis_store',
    'jwt_auth',
]

INSTALLED_APPS = [
    # DJANGO APPS
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.messages',
    'django.contrib.sessions',
    'django.contrib.staticfiles',
    'django.contrib.gis',
    'django.contrib.postgres',

    # LIBRARIES

    # -> 2-factor-auth
    'django_otp',
    'django_otp.plugins.otp_static',
    'django_otp.plugins.otp_email',
    'django_otp.plugins.otp_totp',

    'admin_auto_filters',
    'ordered_model',
    'fixture_magic',
    'autofixture',
    'corsheaders',
    'crispy_forms',
    'django_filters',
    'djangorestframework_camel_case',
    'drf_dynamic_fields',
    'rest_framework',
    'generic_relations',  # DRF Generic relations
    'reversion',
    'storages',
    'django_premailer',
    'django_celery_beat',
    'jsoneditor',
    'drf_yasg',  # API Documentation
    'graphene_django',
    'graphene_graphiql_explorer',
] + [
    '{}.{}.apps.{}Config'.format(
        APPS_DIR.split('/')[-1],
        app,
        ''.join([word.title() for word in app.split('_')]),
    ) for app in LOCAL_APPS
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django_otp.middleware.OTPMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'deep.middleware.RevisionMiddleware',
    'deep.middleware.DeepInnerCacheMiddleware',
    'deep.middleware.RequestMiddleware',
]

ROOT_URLCONF = 'deep.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(APPS_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'deep.context_processor.deep',
            ],
        },
    },
]

WSGI_APPLICATION = 'deep.wsgi.application'


IN_AWS_COPILOT_ECS = not not env('COPILOT_SERVICE_NAME')


if IN_AWS_COPILOT_ECS and env('SERVICE_ENVIRONMENT_TYPE') == 'web':
    ALLOWED_HOSTS.append(
        get_aws_internal_ip(env('SERVICE_ENVIRONMENT_TYPE'))
    )

# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases
if IN_AWS_COPILOT_ECS:
    DBCLUSTER_SECRET = (
        env.json('DEEP_DATABASE_SECRET') or
        fetch_db_credentials_from_secret_arn(env('DEEP_DATABASE_SECRET_ARN'))
    )
    DATABASES = {
        'default': {
            'ENGINE': 'django.contrib.gis.db.backends.postgis',
            # in the workflow environment
            'NAME': DBCLUSTER_SECRET['dbname'],
            'USER': DBCLUSTER_SECRET['username'],
            'PASSWORD': DBCLUSTER_SECRET['password'],
            'HOST': DBCLUSTER_SECRET['host'],
            'PORT': DBCLUSTER_SECRET['port'],
            'OPTIONS': {
                'sslmode': 'require',
                # https://lightsail.aws.amazon.com/ls/docs/en_us/articles/amazon-lightsail-download-ssl-certificate-for-managed-database
                'sslrootcert': os.path.join(BASE_DIR, 'deploy/rds-ca-2019-root.pem'),
            },
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.contrib.gis.db.backends.postgis',
            'NAME': env('DATABASE_NAME'),
            'USER': env('DATABASE_USER'),
            'PASSWORD': env('DATABASE_PASSWORD'),
            'PORT': env('DATABASE_PORT'),
            'HOST': env('DATABASE_HOST'),
            'OPTIONS': {
                'sslmode': 'prefer' if DEBUG else 'require',  # Require ssl in Production
            },
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
    # NOTE: Using django admin panel for password reset/change
    {
        'NAME': 'user.validators.CustomMaximumLengthValidator',
    },
]

# Authentication
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        # TODO: REMOVE THIS!! User client to authenticate.
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        # 'jwt_auth.authentication.JwtAuthentication',
    ),
    'EXCEPTION_HANDLER': 'deep.exception_handler.custom_exception_handler',
    'DEFAULT_RENDERER_CLASSES': [
        'djangorestframework_camel_case.render.CamelCaseJSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': (
        'djangorestframework_camel_case.parser.CamelCaseJSONParser',
        'djangorestframework_camel_case.parser.CamelCaseFormParser',
        'djangorestframework_camel_case.parser.CamelCaseMultiPartParser',
    ),
    'JSON_UNDERSCOREIZE': {
        'no_underscore_before_number': True,
    },

    'DEFAULT_VERSIONING_CLASS':
        'rest_framework.versioning.URLPathVersioning',
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
    ),

    'DEFAULT_PAGINATION_CLASS':
        'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 10000,

    'TEST_REQUEST_DEFAULT_FORMAT': 'json',
}
if DEBUG:
    REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'].append(
        'rest_framework.renderers.BrowsableAPIRenderer'
    )

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

LANGUAGES = (
    ('en-us', 'English (US)'),
    ('es-ES', 'Spanish'),
    ('np', 'Nepali'),
)


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/

# Gallery files Cache-control max-age in seconds
# NOTE: S3 have max 7 days for signed url (https://docs.aws.amazon.com/AmazonS3/latest/API/sigv4-query-string-auth.html) # noqa
GALLERY_FILE_EXPIRE = 60 * 60 * 24 * 2

if env('DJANGO_USE_S3'):
    # AWS S3 Bucket Credentials
    AWS_STORAGE_BUCKET_NAME_STATIC = env('AWS_STORAGE_BUCKET_NAME_STATIC')
    AWS_STORAGE_BUCKET_NAME_MEDIA = env('AWS_STORAGE_BUCKET_NAME_MEDIA')
    # If environment variable are not provided, then EC2 Role will be used.
    if env.json('DEEP_BUCKET_ACCESS_USER_SECRET'):
        AWS_ACCESS_KEY_ID = env.json('DEEP_BUCKET_ACCESS_USER_SECRET')['AccessKeyId']
        AWS_SECRET_ACCESS_KEY = env.json('DEEP_BUCKET_ACCESS_USER_SECRET')['SecretAccessKey']
    else:
        AWS_ACCESS_KEY_ID = env('S3_AWS_ACCESS_KEY_ID')
        AWS_SECRET_ACCESS_KEY = env('S3_AWS_SECRET_ACCESS_KEY')
    AWS_S3_ENDPOINT_URL = env('S3_AWS_ENDPOINT_URL') if DEBUG else None

    AWS_S3_FILE_OVERWRITE = False
    AWS_DEFAULT_ACL = 'private'
    AWS_QUERYSTRING_AUTH = True
    AWS_S3_CUSTOM_DOMAIN = None
    AWS_QUERYSTRING_EXPIRE = GALLERY_FILE_EXPIRE
    AWS_S3_SIGNATURE_VERSION = 's3v4'
    AWS_IS_GZIPPED = True
    GZIP_CONTENT_TYPES = [
        'text/css', 'text/javascript', 'application/javascript', 'application/x-javascript', 'image/svg+xml',
        'application/json',
    ]

    # Static configuration
    STATICFILES_LOCATION = 'static'
    STATIC_URL = "https://%s/%s/" % (AWS_S3_CUSTOM_DOMAIN, STATICFILES_LOCATION)
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

STATICFILES_DIRS = [
    os.path.join(APPS_DIR, 'static'),
]

if IN_AWS_COPILOT_ECS:
    ELASTIC_REDIS_URL = f"redis://{env('ELASTI_CACHE_ADDRESS')}:{env('ELASTI_CACHE_PORT')}"
    CELERY_REDIS_URL = f'{ELASTIC_REDIS_URL}/0'
    DJANGO_CACHE_REDIS_URL = f'{ELASTIC_REDIS_URL}/1'
else:
    CELERY_REDIS_URL = env('CELERY_REDIS_URL')
    DJANGO_CACHE_REDIS_URL = env('DJANGO_CACHE_REDIS_URL')

# CELERY CONFIG "redis://:{password}@{host}:{port}/{db}"

CELERY_BROKER_URL = CELERY_REDIS_URL
CELERY_RESULT_BACKEND = CELERY_REDIS_URL
CELERY_TIMEZONE = TIME_ZONE
CELERY_EVENT_QUEUE_PREFIX = 'deep-celery-'
CELERY_ACKS_LATE = True

CELERY_BEAT_SCHEDULE = {
    'remaining_tabular_generate_columns_image': {
        'task': 'tabular.tasks.remaining_tabular_generate_columns_image',
        # Every 6 hour
        'schedule': crontab(minute=0, hour='*/6'),
    },
    'classify_remaining_lead_previews': {
        'task': 'lead.tasks.classify_remaining_lead_previews',
        # Every 3 hours
        'schedule': crontab(minute=0, hour='*/3'),
    },
    'project_generate_stats': {
        'task': 'project.tasks.generate_project_stats_cache',
        # Every 5 min
        'schedule': crontab(minute="*/5"),
    },
}

if IN_AWS_COPILOT_ECS:
    CELERY_BEAT_SCHEDULE.update({
        'push_celery_cloudwatch_metric': {
            'task': 'deep.tasks.put_celery_query_metric',
            # Every minute
            'schedule': crontab(minute='*/1'),
        },
    })

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': DJANGO_CACHE_REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'dj_cache-',
    },
    'local-memory': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# RELIEF WEB
RELIEFWEB_APPNAME = 'thedeep.io'

# HID CONFIGS [NOTE: Update config in React too]
HID_CLIENT_ID = env('HID_CLIENT_ID')
HID_CLIENT_REDIRECT_URL = env('HID_CLIENT_REDIRECT_URL')
HID_AUTH_URI = env('HID_AUTH_URI')


def add_username_attribute(record):
    """
    Append username(email) to logs
    """
    record.username = 'UNK_USER'
    if hasattr(record, 'request'):
        if hasattr(record.request, 'user') and\
                not record.request.user.is_anonymous:
            record.username = record.request.user.username
        else:
            record.username = 'Anonymous_User'
    return True


# pdfminer can log heavy logs
logging.getLogger("pdfminer").setLevel(logging.WARNING)

if IN_AWS_COPILOT_ECS:
    format_args = [env('SERVICE_ENVIRONMENT_TYPE')]
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
                'format': '%(asctime)s DJANGO-{}: - %(levelname)s - %(name)s - [%(username)s] %(message)s'.format(
                    *format_args,
                ),
                'datefmt': '%Y-%m-%dT%H:%M:%S',
            },
            'profiling': {
                'format': '%(asctime)s PROFILING-{}: %(message)s'.format(*format_args),
                'datefmt': '%Y-%m-%dT%H:%M:%S',
            },
        },
        'handlers': {
            'SysLog': {
                'level': 'INFO',
                'class': 'logging.StreamHandler',
                'filters': ['add_username_attribute'],
                'formatter': 'simple',
            },
            'ProfilingSysLog': {
                'level': 'INFO',
                'class': 'logging.StreamHandler',
                'formatter': 'profiling',
            },
        },
        'loggers': {
            **{
                app: {
                    'handlers': ['SysLog'],
                    'propagate': True,
                }
                for app in LOCAL_APPS + ['deep', 'utils', 'celery', 'django']
            },
            'profiling': {
                'handlers': ['ProfilingSysLog'],
                'level': 'INFO',
                'propagate': True,
            },
        }
    }
else:
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'colored_verbose': {
                '()': 'colorlog.ColoredFormatter',
                'format': "%(log_color)s%(levelname)-8s%(red)s%(module)-8s%(reset)s %(asctime)s %(blue)s%(message)s"
            },
        },
        'handlers': {
            'console': {
                'level': 'INFO',
                'class': 'logging.StreamHandler',
            },
            'colored_console': {
                'level': 'INFO',
                'class': 'logging.StreamHandler',
                'formatter': 'colored_verbose'
            },
        },
        'loggers': {
            **{
                app: {
                    'handlers': ['colored_console'],
                    'level': 'INFO',
                    'propagate': True,
                }
                for app in LOCAL_APPS + ['deep', 'utils', 'celery', 'django']
            },
            'profiling': {
                'handlers': ['colored_console'],
                'level': 'DEBUG',
                'propagate': True,
            },
        },
    }

# CORS CONFIGS
if DEBUG:
    CORS_ORIGIN_ALLOW_ALL = True
else:
    # Restrict to thedeep.io 1 level subdomains only in Production
    CORS_ORIGIN_REGEX_WHITELIST = [
        r"^https://[\w-]+\.thedeep\.io$",
    ]

CORS_URLS_REGEX = r'(^/api/.*$)|(^/media/.*$)|(^/graphql$)'
CORS_ALLOW_CREDENTIALS = True

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
    'sentry-trace',
)

# Email CONFIGS
USE_SES_EMAIL_CONFIG = env('USE_SES_EMAIL_CONFIG')
DEFAULT_FROM_EMAIL = EMAIL_FROM = env('EMAIL_FROM')
ADMINS = tuple(parseaddr(email) for email in env.list('DJANGO_ADMINS'))

if USE_SES_EMAIL_CONFIG and not TESTING:
    """
    Use AWS SES
    """
    EMAIL_BACKEND = 'django_ses.SESBackend'
    # If environment variable are not provided, then EC2 Role will be used.
    AWS_SES_ACCESS_KEY_ID = env('SES_AWS_ACCESS_KEY_ID')
    AWS_SES_SECRET_ACCESS_KEY = env('SES_AWS_SECRET_ACCESS_KEY')
else:
    """
    DUMP THE EMAIL TO CONSOLE
    """
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'


# Gallery files Cache-control max-age - 1hr from s3
MAX_FILE_CACHE_AGE = GALLERY_FILE_EXPIRE - (60 * 60)

# Connector cache age
CONNECTOR_CACHE_AGE = 12 * 60 * 60  # 12 Hours

# Lead website fetch timeout
LEAD_WEBSITE_FETCH_TIMEOUT = 15

# Max login attempts to allow before using captcha
MAX_LOGIN_ATTEMPTS_FOR_CAPTCHA = 3
# Max login attempts to allow before preventing further logins
MAX_LOGIN_ATTEMPTS = 10

# https://docs.hcaptcha.com/#integration-testing-test-keys
HCAPTCHA_SECRET = env('HCAPTCHA_SECRET')

# Sentry Config
SENTRY_DSN = env('SENTRY_DSN')
SENTRY_SAMPLE_RATE = env('SENTRY_SAMPLE_RATE')

if SENTRY_DSN:
    SENTRY_CONFIG = {
        'dsn': SENTRY_DSN,
        'send_default_pii': True,
        'release': sentry.fetch_git_sha(BASE_DIR),
        'environment': DEEP_ENVIRONMENT,
        'debug': DEBUG,
        'tags': {
            'site': DJANGO_API_HOST,
        },
    }
    sentry.init_sentry(
        app_type='API',
        **SENTRY_CONFIG,
    )

# DEEPL Config
DEEPL_DOMAINS = {
    'nightly': 'https://deepl-nightly.thedeep.io',
    'alpha': 'https://deepl-alpha.thedeep.io',
    'beta': 'https://deepl.togglecorp.com',
    'development': env('DEEPL_DOMAIN'),
}

DEEPL_DOMAIN = DEEPL_DOMAINS.get(DEEP_ENVIRONMENT, DEEPL_DOMAINS['alpha'])
DEEPL_API = DEEPL_DOMAIN + '/api'

# Token timeout days
TOKEN_DEFAULT_RESET_TIMEOUT_DAYS = 7
PROJECT_REQUEST_RESET_TIMEOUT_DAYS = 7

JSON_EDITOR_INIT_JS = 'js/jsoneditor-init.js'
LOGIN_URL = '/admin/login'

OTP_TOTP_ISSUER = f'Deep Admin {DEEP_ENVIRONMENT.title()}'
OTP_EMAIL_SENDER = EMAIL_FROM
OTP_EMAIL_SUBJECT = 'Deep Admin OTP Token'

REDOC_SETTINGS = {
    'LAZY_RENDERING': True,
    'HIDE_HOSTNAME': True,
    'NATIVE_SCROLLBARS': True,
    'EXPAND_RESPONSES': [],
}

OPEN_API_DOCS_TIMEOUT = 86400  # 24 Hours

ANALYTICAL_STATEMENT_COUNT = 30  # max no of analytical statement that can be created
ANALYTICAL_ENTRIES_COUNT = 50  # max no of entries that can be created in analytical_statement
DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

# DEBUG TOOLBAR CONFIGURATION
DEBUG_TOOLBAR_CONFIG = {
    'DISABLE_PANELS': [
        'debug_toolbar.panels.sql.SQLPanel',
        'debug_toolbar.panels.staticfiles.StaticFilesPanel',
        'debug_toolbar.panels.redirects.RedirectsPanel',
        'debug_toolbar.panels.templates.TemplatesPanel',
    ],
}
DEBUG_TOOLBAR_PANELS = [
    "debug_toolbar.panels.versions.VersionsPanel",
    "debug_toolbar.panels.timer.TimerPanel",
    "debug_toolbar.panels.settings.SettingsPanel",
    "debug_toolbar.panels.headers.HeadersPanel",
    "debug_toolbar.panels.request.RequestPanel",
    "debug_toolbar.panels.sql.SQLPanel",
    "debug_toolbar.panels.staticfiles.StaticFilesPanel",
    "debug_toolbar.panels.templates.TemplatesPanel",
    "debug_toolbar.panels.cache.CachePanel",
    "debug_toolbar.panels.signals.SignalsPanel",
    # ENABLING THIS WILL REMOVE LOGS FROM stdout "debug_toolbar.panels.logging.LoggingPanel",
    "debug_toolbar.panels.redirects.RedirectsPanel",
    "debug_toolbar.panels.profiling.ProfilingPanel",
]

if DEBUG and env('DOCKER_HOST_IP') and not TESTING:
    # https://github.com/flavors/django-graphiql-debug-toolbar#installation
    # FIXME: If mutation are triggered twice https://github.com/flavors/django-graphiql-debug-toolbar/pull/12/files
    # FIXME: All request are triggered twice. Creating multiple entries in admin panel as well.
    # # JUST FOR Graphiql
    # INSTALLED_APPS += ['debug_toolbar', 'graphiql_debug_toolbar']
    # MIDDLEWARE = ['deep.middleware.DebugToolbarMiddleware'] + MIDDLEWARE
    # # JUST FOR DRF
    # INSTALLED_APPS += ['debug_toolbar']
    # MIDDLEWARE = ['debug_toolbar.middleware.DebugToolbarMiddleware'] + MIDDLEWARE
    # INTERNAL_IPS = [env('DOCKER_HOST_IP')]
    pass

# https://docs.djangoproject.com/en/3.1/ref/settings/#std:setting-APPEND_SLASH
APPEND_SLASH = True

# Security Header configuration
SESSION_COOKIE_NAME = f'deep-{DEEP_ENVIRONMENT}-sessionid'
CSRF_COOKIE_NAME = f'deep-{DEEP_ENVIRONMENT}-csrftoken'
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
CSP_DEFAULT_SRC = ["'self'"]
SECURE_REFERRER_POLICY = 'same-origin'
if HTTP_PROTOCOL == 'https':
    SESSION_COOKIE_NAME = f'__Secure-{SESSION_COOKIE_NAME}'
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    # SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 30  # TODO: Increase this slowly
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    # NOTE: Client needs to read CSRF COOKIE.
    # CSRF_COOKIE_NAME = f'__Secure-{CSRF_COOKIE_NAME}'
    # CSRF_COOKIE_SECURE = True
    # CSRF_COOKIE_HTTPONLY = True
    CSRF_TRUSTED_ORIGINS = [
        DEEPER_FRONTEND_HOST,
        DEEPER_FRONTEND_ARY_HOST,  # TODO: Remove this later
        DJANGO_API_HOST,
    ]

# https://docs.djangoproject.com/en/3.2/ref/settings/#std:setting-CSRF_USE_SESSIONS
# CSRF_USE_SESSIONS = env('CSRF_TRUSTED_ORIGINS')
# https://docs.djangoproject.com/en/3.2/ref/settings/#std:setting-SESSION_COOKIE_DOMAIN
SESSION_COOKIE_DOMAIN = env('SESSION_COOKIE_DOMAIN')
# https://docs.djangoproject.com/en/3.2/ref/settings/#csrf-cookie-domain
CSRF_COOKIE_DOMAIN = env('CSRF_COOKIE_DOMAIN')

# DEEPL Config
DEEPL_EXTRACTOR_URL = env('DEEPL_EXTRACTOR_URL')
DEEPL_EXTRACTOR_CALLBACK_URL = env('DEEPL_EXTRACTOR_CALLBACK_URL')

# Graphene configs
# WHITELIST following nodes from authentication checks
GRAPHENE_NODES_WHITELIST = (
    '__schema',
    '__type',
    '__typename',
    # custom nodes...
    'login',
    'loginWithHid',
    'register',
    'resetPassword',
    'projectExploreStats',
    'publicProjects',
    'publicProjectsByRegion',
    'publicAnalysisFrameworks',
    'publicOrganizations',
)

# https://docs.graphene-python.org/projects/django/en/latest/settings/
GRAPHENE = {
    'ATOMIC_MUTATIONS': True,
    'SCHEMA': 'deep.schema.schema',
    'SCHEMA_OUTPUT': 'schema.json',  # defaults to schema.json,
    'CAMELCASE_ERRORS': True,
    'SCHEMA_INDENT': 2,  # Defaults to None (displays all data on a single line)
    'MIDDLEWARE': [
        'utils.graphene.middleware.DisableIntrospectionSchemaMiddleware',
        'utils.sentry.SentryGrapheneMiddleware',
        'utils.graphene.middleware.WhiteListMiddleware',
    ],
}
if DEBUG:
    GRAPHENE['MIDDLEWARE'].append('graphene_django.debug.DjangoDebugMiddleware')

GRAPHENE_DJANGO_EXTRAS = {
    'DEFAULT_PAGINATION_CLASS': 'graphene_django_extras.paginations.PageGraphqlPagination',
    'DEFAULT_PAGE_SIZE': 20,
    'MAX_PAGE_SIZE': 50,
}

if DEEP_ENVIRONMENT in ['production']:
    GRAPHENE['MIDDLEWARE'].append('deep.middleware.DisableIntrospectionSchemaMiddleware')
