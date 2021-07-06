"""
Django settings for deep project.
"""
import os
import sys
import logging
from celery.schedules import crontab

from utils import sentry


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APPS_DIR = os.path.join(BASE_DIR, 'apps')
TEMP_DIR = '/tmp'

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.11/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    '=p5!pos4^@$tb1yi@++o5_s)ya@62odvk_mf--#8ozaw0wnc0q')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DJANGO_DEBUG', 'True').lower() == 'true'

DEEP_ENVIRONMENT = os.environ.get('DEEP_ENVIRONMENT', 'development')

ALLOWED_HOSTS = [os.environ.get('DJANGO_ALLOWED_HOST', '*')]

DEEPER_FRONTEND_HOST = os.environ.get('FRONTEND_HOST', 'localhost:3000')
DJANGO_API_HOST = os.environ.get('DJANGO_ALLOWED_HOST', 'localhost:8000')

DEEPER_SITE_NAME = os.environ.get('DEEPER_SITE_NAME', 'DEEPER')
HTTP_PROTOCOL = os.environ.get('DEEP_HTTPS', 'http')

# See if we are inside a test environment (pytest)
TESTING = any([
    arg in sys.argv for arg in [
        'test',
        'pytest', '/usr/local/bin/pytest',
        'py.test', '/usr/local/bin/py.test',
        '/usr/local/lib/python3.6/dist-packages/py/test.py',
    ]
    # Provided by pytest-xdist
]) or os.environ.get('PYTEST_XDIST_WORKER') is not None

PROFILE = os.environ.get('PROFILE', 'false').lower() == 'true'

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


# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': os.environ.get('DATABASE_NAME', 'postgres'),
        'USER': os.environ.get('DATABASE_USER', 'postgres'),
        'PASSWORD': os.environ.get('DATABASE_PASSWORD', 'postgres'),
        'PORT': os.environ.get('DATABASE_PORT', '5432'),
        'HOST': os.environ.get('DATABASE_HOST', 'db'),
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
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'jwt_auth.authentication.JwtAuthentication',
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

if os.environ.get('DJANGO_USE_S3', 'False').lower() == 'true':
    # AWS S3 Bucket Credentials
    AWS_STORAGE_BUCKET_NAME_STATIC = os.environ['DJANGO_AWS_STORAGE_BUCKET_NAME_STATIC']
    AWS_STORAGE_BUCKET_NAME_MEDIA = os.environ['DJANGO_AWS_STORAGE_BUCKET_NAME_MEDIA']
    # If environment variable are not provided, then EC2 Role will be used.
    AWS_ACCESS_KEY_ID = os.environ.get('S3_AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.environ.get('S3_AWS_SECRET_ACCESS_KEY')
    AWS_S3_ENDPOINT_URL = os.environ.get('S3_AWS_ENDPOINT_URL') if DEBUG else None

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

# CELERY CONFIG "redis://:{password}@{host}:{port}/{db}"
CELERY_REDIS_URL = os.environ.get('CELERY_REDIS_URL', 'redis://redis:6379/0')
CELERY_BROKER_URL = CELERY_REDIS_URL
CELERY_RESULT_BACKEND = CELERY_REDIS_URL
CELERY_TIMEZONE = TIME_ZONE
CELERY_ACKS_LATE = True

CELERY_BEAT_SCHEDULE = {
    'remaining_tabular_generate_columns_image': {
        'task': 'tabular.tasks.remaining_tabular_generate_columns_image',
        # Every 6 hour
        'schedule': crontab(minute=0, hour="*/6"),
    },
    'classify_remaining_lead_previews': {
        'task': 'lead.tasks.classify_remaining_lead_previews',
        # Every 3 hours
        'schedule': crontab(minute=0, hour="*/3"),
    },
    'project_generate_stats': {
        'task': 'project.tasks.generate_project_stats_cache',
        # Every 1 hour
        'schedule': crontab(minute=0, hour="*/1"),
    },
}

# REDIS STORE CONFIG "redis://:{password}@{host}:{port}/{db}"
# CHANNEL_REDIS_URL = os.environ.get('CHANNEL_REDIS_URL', 'redis://redis:6379/1')
# CHANNELS CONFIG
# CHANNEL_LAYERS = {
#    'default': {
#        'BACKEND': 'asgi_redis.core.RedisChannelLayer',
#        'CONFIG': {
#            'hosts': [CHANNEL_REDIS_URL],
#        },
#        'ROUTING': 'deep.routing.channel_routing',
#    },
# }

DJANGO_CACHE_REDIS_URL = os.environ.get('DJANGO_CACHE_REDIS_URL', 'redis://redis:6379/2')
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": DJANGO_CACHE_REDIS_URL,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
        "KEY_PREFIX": "dj_cache-",
    },
}

TEST_DIR = os.path.join(BASE_DIR, 'deep/test_files')

# RELIEF WEB
RELIEFWEB_APPNAME = 'thedeep.io'

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

if os.environ.get('USE_PAPERTRAIL', 'False').lower() == 'true':
    format_args = (
        os.environ.get('EBS_HOSTNAME', 'UNK_HOST'),
        os.environ.get('EBS_ENV_TYPE', 'UNK_ENV'),
    )
    papertrail_address = (os.environ.get('PAPERTRAIL_HOST'), int(os.environ.get('PAPERTRAIL_PORT')))
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
                'format': '%(asctime)s {} DJANGO-{}: - %(levelname)s - %(name)s - [%(username)s] %(message)s'.format(
                    *format_args,
                ),
                'datefmt': '%Y-%m-%dT%H:%M:%S',
            },
            'profiling': {
                'format': '%(asctime)s {} PROFILING-{}: %(message)s'.format(*format_args),
                'datefmt': '%Y-%m-%dT%H:%M:%S',
            },
        },
        'handlers': {
            'SysLog': {
                'level': 'INFO',
                'class': 'logging.handlers.SysLogHandler',
                'filters': ['add_username_attribute'],
                'formatter': 'simple',
                'address': papertrail_address,
            },
            'ProfilingSysLog': {
                'level': 'INFO',
                'class': 'logging.handlers.SysLogHandler',
                'formatter': 'profiling',
                'address': papertrail_address,
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
        'handlers': {
            'console': {
                'level': 'INFO',
                'class': 'logging.StreamHandler',
            },
        },
        'loggers': {
            'django': {
                'handlers': ['console'],
                'level': 'INFO',
                'propagate': True,
            },
            'profiling': {
                'handlers': ['console'],
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
        r"^https://\w+\.thedeep\.io$",
    ]

CORS_URLS_REGEX = r'(^/api/.*$)|(^/media/.*$)'

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

# Email CONFIGS (NOT USED)
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', 'deep1234')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT') or 587)
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True').lower() == 'true'

# Email CONFIGS
USE_EMAIL_CONFIG = os.environ.get('USE_EMAIL_CONFIG', 'False').lower() == 'true'
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', 'deepnotifications1@gmail.com')
EMAIL_FROM = '{}DEEP Admin <{}>'.format(
    f'[{DEEP_ENVIRONMENT.upper()}] ' if DEEP_ENVIRONMENT.lower() != 'beta' else '',
    EMAIL_HOST_USER,
)
DEFAULT_FROM_EMAIL = EMAIL_FROM
ADMINS = [('Ewan', 'ewanogle@gmail.com'), ('Togglecorp', 'info@togglecorp.com')]

if TESTING or not USE_EMAIL_CONFIG:
    """
    DUMP THE EMAIL TO CONSOLE
    """
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
else:
    """
    Use AWS SES
    """
    EMAIL_BACKEND = 'django_ses.SESBackend'
    # If environment variable are not provided, then EC2 Role will be used.
    AWS_SES_ACCESS_KEY_ID = os.environ.get('SES_AWS_ACCESS_KEY_ID')
    AWS_SES_SECRET_ACCESS_KEY = os.environ.get('SES_AWS_SECRET_ACCESS_KEY')

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
HCAPTCHA_SECRET = os.environ.get('HCAPTCHA_SECRET', '0x0000000000000000000000000000000000000000')

# Sentry Config
SENTRY_DSN = os.environ.get('SENTRY_DSN')

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
    'development': os.environ.get('DEEPL_DOMAIN', 'http://192.168.31.92:8010'),
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

if DEBUG and 'DOCKER_HOST_IP' in os.environ:
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE = ['debug_toolbar.middleware.DebugToolbarMiddleware'] + MIDDLEWARE
    INTERNAL_IPS = [os.environ['DOCKER_HOST_IP']]


# https://docs.djangoproject.com/en/3.1/ref/settings/#std:setting-APPEND_SLASH
APPEND_SLASH = False

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
    CSRF_COOKIE_NAME = f'__Secure-{CSRF_COOKIE_NAME}'
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 30  # TODO: Increase this slowly
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SESSION_COOKIE_HTTPONLY = True
    CSRF_COOKIE_HTTPONLY = True

# https://docs.djangoproject.com/en/3.2/ref/settings/#std:setting-CSRF_USE_SESSIONS
CSRF_USE_SESSIONS = os.environ.get('CSRF_TRUSTED_ORIGINS', 'False').lower() == 'true'
# https://docs.djangoproject.com/en/3.2/ref/settings/#std:setting-SESSION_COOKIE_DOMAIN
SESSION_COOKIE_DOMAIN = os.environ.get('SESSION_COOKIE_DOMAIN', 'localhost')
# https://docs.djangoproject.com/en/3.2/ref/settings/#csrf-cookie-domain
CSRF_COOKIE_DOMAIN = os.environ.get('CSRF_COOKIE_DOMAIN', 'localhost')


# WHITELIST following nodes from authentication checks
GRAPHENE_NODES_WHITELIST = (
    '__schema',
    '__type',
    '__typename',
    # custom nodes...
    'login',
    'register',
    'resetPassword',
)

# https://docs.graphene-python.org/projects/django/en/latest/settings/
GRAPHENE = {
    'ATOMIC_MUTATIONS': True,
    'SCHEMA': 'deep.schema.schema',
    'SCHEMA_OUTPUT': 'schema.json',  # defaults to schema.json,
    'SCHEMA_INDENT': 2,  # Defaults to None (displays all data on a single   line)
    'MIDDLEWARE': [
        'utils.graphene.middleware.WhiteListMiddleware',
    ],
}

GRAPHENE_DJANGO_EXTRAS = {
    'DEFAULT_PAGINATION_CLASS': 'graphene_django_extras.paginations.PageGraphqlPagination',
    'DEFAULT_PAGE_SIZE': 20,
    'MAX_PAGE_SIZE': 50,
}

if DEEP_ENVIRONMENT in ['production']:
    GRAPHENE['MIDDLEWARE'].append('deep.middleware.DisableIntrospectionSchemaMiddleware')
