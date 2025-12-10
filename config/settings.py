"""
Django settings for School Portal project.
Multi-centre school management system with role-based access control.
"""

from pathlib import Path
from datetime import timedelta
from decouple import config, Csv
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-CHANGE-THIS-IN-PRODUCTION')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=Csv())

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third party apps
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'django_filters',
    'corsheaders',
    'drf_spectacular',
    
    # Local apps
    'apps.users',
    'apps.centres',
    'apps.classes',
    'apps.homework',
    'apps.calendar',
    'apps.whiteboard',
    'apps.core',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.core.middleware.CentreFilterMiddleware',
]

ROOT_URLCONF = 'config.urls'

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

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

# Channel Layers (for WebSocket support in Phase 2+)
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [config('REDIS_URL', default='redis://localhost:6379/0')],
        },
    },
}

# For production with Redis password, use:
# REDIS_URL=redis://:password@redis:6379/0
# For development without password, use:
# REDIS_URL=redis://localhost:6379/0

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME', default='school_portal'),
        'USER': config('DB_USER', default='postgres'),
        'PASSWORD': config('DB_PASSWORD', default='postgres'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
    }
}

# Custom User Model
AUTH_USER_MODEL = 'users.User'

# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST Framework Configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
    'PAGE_SIZE_QUERY_PARAM': 'page_size',  # Allow client to override page size with ?page_size=50
    'MAX_PAGE_SIZE': 100,  # Maximum allowed page size
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'EXCEPTION_HANDLER': 'rest_framework.views.exception_handler',
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# DRF Spectacular Settings (OpenAPI 3.0)
SPECTACULAR_SETTINGS = {
    'TITLE': 'School Portal API',
    'DESCRIPTION': '''
# School Portal API Documentation

A comprehensive multi-centre school management system with role-based access control.

## Authentication

This API uses JWT (JSON Web Token) authentication. To authenticate:

1. Obtain tokens by calling `/api/auth/login/` with email and password
2. Use the access token in the Authorization header: `Bearer <access_token>`
3. Refresh tokens when they expire using `/api/auth/refresh/`

## User Roles

- **SUPER_ADMIN**: Full system access across all centres
- **CENTRE_MANAGER**: Manage one centre (classes, teachers, students)
- **TEACHER**: Access assigned classes only (homework, grading, whiteboard)
- **STUDENT**: Access own homework, classes, and events
- **PARENT**: View linked students' information

## Multi-Centre Support

The system supports multiple centres with full data isolation. Users (except Super Admin) 
only have access to data from their assigned centre.

## Features

### Phase 1: Core Features
- User management and authentication
- Centre management with holidays and term dates
- Class management with teacher assignments
- Homework creation, submission, and grading
- Calendar and event management

### Phase 2: Enhanced Features
- Real-time whiteboard collaboration (WebSocket)
- Role-specific dashboards
- Parent-student linking
- Student profiles with privacy protection

### Phase 3: Advanced Features
- Analytics and reporting
- Email notifications
- Background task processing
- SMS integration (optional)

## Rate Limiting

- Anonymous requests: 100 per hour
- Authenticated requests: 1000 per hour

## Pagination

List endpoints return paginated results (20 items per page by default).
Use `?page=2` to navigate pages.

## File Uploads

Maximum file size: 10MB
Supported formats: PDF, DOC, DOCX, TXT, JPG, JPEG, PNG, ZIP
    ''',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'SCHEMA_PATH_PREFIX': '/api/',
    
    # Contact and License
    'CONTACT': {'email': 'support@schoolportal.com'},
    'LICENSE': {'name': 'Proprietary'},
    
    # Security schemes
    'SECURITY': [{'Bearer': []}],
    'APPEND_COMPONENTS': {
        'securitySchemes': {
            'Bearer': {
                'type': 'http',
                'scheme': 'bearer',
                'bearerFormat': 'JWT',
                'description': 'Enter JWT token obtained from /api/auth/login/'
            }
        }
    },
    
    # Tags for organizing endpoints
    'TAGS': [
        {'name': 'Authentication', 'description': 'Login, logout, token refresh, password reset'},
        {'name': 'Users', 'description': 'User management and profiles'},
        {'name': 'Centres', 'description': 'Centre management, holidays, term dates'},
        {'name': 'Classes', 'description': 'Class management, enrolments, teacher assignments'},
        {'name': 'Homework', 'description': 'Homework assignments and submissions'},
        {'name': 'Calendar', 'description': 'Events and calendar management'},
        {'name': 'Whiteboard', 'description': 'Real-time whiteboard sessions'},
        {'name': 'Dashboards', 'description': 'Role-specific dashboard data'},
        {'name': 'Analytics', 'description': 'Reports and analytics'},
    ],
    
    # Swagger UI settings
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        'persistAuthorization': True,
        'displayOperationId': False,
        'filter': True,
        'docExpansion': 'none',
        'defaultModelsExpandDepth': 2,
        'defaultModelExpandDepth': 2,
    },
    
    # Redoc settings
    'REDOC_UI_SETTINGS': {
        'hideDownloadButton': False,
        'disableSearch': False,
    },
    
    # Enum naming
    'ENUM_NAME_OVERRIDES': {
        'UserRoleEnum': 'apps.users.models.User.Role',
        'SubmissionStatusEnum': 'apps.homework.models.Submission.Status',
        'EventTypeEnum': 'apps.calendar.models.Event.EventType',
    },
}

# JWT Settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=config('JWT_ACCESS_TOKEN_LIFETIME_MINUTES', default=60, cast=int)),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=config('JWT_REFRESH_TOKEN_LIFETIME_DAYS', default=7, cast=int)),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
}

# CORS Settings
CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    default='http://localhost:3000,http://localhost:8000',
    cast=Csv()
)
CORS_ALLOW_CREDENTIALS = True

# For development: Allow all origins (less secure, only for development!)
if DEBUG:
    CORS_ALLOW_ALL_ORIGINS = True
    # Also add specific origins for WebSocket
    CORS_ALLOWED_ORIGIN_REGEXES = [
        r"^http://\d+\.\d+\.\d+\.\d+:\d+$",  # Allow any IP with port
        r"^http://\d+\.\d+\.\d+\.\d+$",       # Allow any IP without port
        r"^ws://\d+\.\d+\.\d+\.\d+:\d+$",     # WebSocket with port
        r"^ws://\d+\.\d+\.\d+\.\d+$",         # WebSocket without port
    ]

# CSRF Trusted Origins (for production)
CSRF_TRUSTED_ORIGINS = config(
    'CSRF_TRUSTED_ORIGINS',
    default='http://localhost:3000,http://localhost:8000',
    cast=Csv()
)

# Security Settings (for production)
if not DEBUG:
    SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=True, cast=bool)
    SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', default=True, cast=bool)
    CSRF_COOKIE_SECURE = config('CSRF_COOKIE_SECURE', default=True, cast=bool)
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    X_FRAME_OPTIONS = 'DENY'

# File Upload Settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10 MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10 MB

# Email Configuration (Phase 3)
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@schoolportal.com')

# Redis Configuration (Phase 2+)
REDIS_URL = config('REDIS_URL', default='redis://localhost:6379/0')

# Celery Configuration (Phase 3)
CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default='redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        'apps': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Create logs directory if it doesn't exist
LOGS_DIR = BASE_DIR / 'logs'
if not LOGS_DIR.exists():
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
