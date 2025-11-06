import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Security Settings
SECRET_KEY = 'django-insecure-your-secret-key-here-change-in-production'
DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'yourdomain.com']

# Application definition
INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'exam.apps.ExamConfig',
    'django_extensions',
    
    
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'exam.middleware.BlockLoginForAuthenticated',
]



SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_AGE = 5  # detik, sementara aja buat test
SESSION_SAVE_EVERY_REQUEST = True



ROOT_URLCONF = 'cbt_system.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
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


JAZZMIN_SETTINGS = {
    "site_title": "RPLCommunity Admin",
    "site_header": "RPLCommunity Dashboard",

    "show_sidebar": True,
    "navigation_expanded": True,


    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",
        "exams.Exam": "fas fa-file-alt",
        "exams.Question": "fas fa-question-circle",
    },

    # === INI BAGIAN SIDEBAR ===
    "side_menu": [

        # Dashboard tetap paling atas
        {"label": "Dashboard", "url": "admin:index", "icon": "fas fa-home"},

        # Menu User Management
        {
            "label": "User Management",
            "icon": "fas fa-users",
            "children": [
                {"model": "exam.CustomUser"},
                {"label": "Add User", "url": "exam:admin_user_create", "icon": "fas fa-user-plus"},
                # nanti tinggal tambah Token, Log, dll disini
            ],
        },

        # Menu untuk Exam
        {
            "label": "Exams",
            "icon": "fas fa-file-alt",
            "children": [
                {"model": "exams.Exam"},
                {"model": "exams.Question"},
            ]
        },
    ],
}



WSGI_APPLICATION = 'cbt_system.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# For Production (PostgreSQL example)
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': 'cbt_system',
#         'USER': 'cbt_user',
#         'PASSWORD': 'securepassword123',
#         'HOST': 'localhost',
#         'PORT': '5432',
#     }
# }

# Password validation
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
AUTH_USER_MODEL = 'exam.CustomUser'

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')


# Login URLs
LOGIN_URL = 'exam:login'
LOGIN_REDIRECT_URL = 'exam:student_dashboard'
LOGOUT_REDIRECT_URL = 'exam:login'
LOGOUT_REDIRECT_ALLOWED_METHODS = ['GET', 'POST']

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]



# Security Settings (for production)
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# Custom Admin Settings
ADMIN_SITE_HEADER = "CBT System Administration"
ADMIN_SITE_TITLE = "CBT System Admin"
ADMIN_INDEX_TITLE = "Welcome to CBT System Administration Panel"

# Session settings
SESSION_COOKIE_AGE = 1209600  # 2 weeks
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
# di settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}