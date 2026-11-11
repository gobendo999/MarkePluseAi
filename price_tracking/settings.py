"""
Django settings for price_tracking project.
MarketPulse AI — Competitor Intelligence & Price Tracking SaaS
"""

from pathlib import Path
from datetime import timedelta
import os
from dotenv import load_dotenv
 


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file
load_dotenv(BASE_DIR / '.env')

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    'django-insecure-marketpulse-secret-key-development-mode-2026'
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = ['*']

# Application definition
INSTALLED_APPS = [
    # 1. Modern Admin Interface (Must be before django.contrib.admin)
    'jazzmin',

    # 2. Django Core Apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # 3. Third-party Libraries
    'corsheaders',
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'drf_spectacular',
    'django_filters',

    # 4. Domain / Internal Apps
    'apps.accounts.apps.AccountsConfig',
    'apps.products.apps.ProductsConfig',
    'apps.scraper.apps.ScraperConfig',
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
    'price_tracking.middleware.ExecutionTimeLoggingMiddleware'
    ]

ROOT_URLCONF = 'price_tracking.urls'

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
            ],
        },
    },
]

WSGI_APPLICATION = 'price_tracking.wsgi.application'

# ==============================================================================
# Database Configuration (PostgreSQL / Supabase or SQLite fallback)
if os.environ.get('DB_HOST'):
    DATABASES = {
        'default': {
            'ENGINE': os.environ.get('DB_ENGINE', 'django.db.backends.postgresql'),
            'NAME': os.environ.get('DB_NAME', 'postgres'),
            'USER': os.environ.get('DB_USER', 'postgres'),
            'PASSWORD': os.environ.get('DB_PASSWORD', ''),
            'HOST': os.environ.get('DB_HOST'),
            'PORT': os.environ.get('DB_PORT', '5432'),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Custom User Model (Topic 21)
AUTH_USER_MODEL = 'accounts.CustomUser'

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

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ==============================================================================
# REST FRAMEWORK & OPENAPI SETTINGS (Topics 35-41)
# ==============================================================================
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ),
    'DEFAULT_THROTTLE_CLASSES': (
        'apps.accounts.throttles.TierBasedUserRateThrottle',
    ),

}

# Swagger & OpenAPI Documentation (Topic 41)
SPECTACULAR_SETTINGS = {
    'TITLE': 'MarketPulse AI — Competitor Intelligence & Price Tracking API',
    'DESCRIPTION': (
        'High-throughput competitor price tracking, asynchronous scraping pipeline, '
        'LLM sentiment intelligence, and SaaS subscription billing engine.'
    ),
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
}

# JWT Authentication Config (Topic 37)
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=14),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# CORS Configuration
CORS_ALLOW_ALL_ORIGINS = True

# ==============================================================================
# JAZZMIN ADMIN DASHBOARD CONFIGURATION (Topic 19)
# ==============================================================================
JAZZMIN_SETTINGS = {
    'site_title': 'MarketPulse AI',
    'site_header': 'MarketPulse AI Admin',
    'site_brand': 'MarketPulse AI',
    'welcome_sign': 'Welcome to MarketPulse AI Intelligence Hub',
    'copyright': 'MarketPulse AI Technologies',
    'search_model': ['accounts.CustomUser'],
    'user_avatar': None,
    'topmenu_links': [
        {'name': 'Dashboard Home', 'url': 'admin:index', 'permissions': ['auth.view_user']},
        {'name': 'Swagger API Docs', 'url': '/api/docs/', 'new_window': True},
    ],
    'show_sidebar': True,
    'navigation_expanded': True,
    'icons': {
        'auth': 'fas fa-users-cog',
        'accounts.CustomUser': 'fas fa-user-shield',
    },
    'default_icon_parents': 'fas fa-chevron-circle-right',
    'default_icon_children': 'fas fa-circle',
}
# কোন ব্রোকারে চিরকুট জমা হবে (ডিফল্ট Redis)
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
# ডাটা ফরম্যাট হবে নিরাপদ JSON
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
# কোনো টাস্ক শুরু হলে তার স্টেট ট্র্যাক করা
CELERY_TASK_TRACK_STARTED = True