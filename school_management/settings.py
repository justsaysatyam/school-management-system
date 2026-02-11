"""
Django settings for school_management project.
Mid Point School - School Management System
"""

from pathlib import Path
import os
import sys
import dj_database_url


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-(5w%d1g^st1z2^#ov6dzmmu%qdq63o-#x#)z0ly&g^_5afp@-u'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['.vercel.app', '127.0.0.1', 'localhost', '*']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'school_management.urls'

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

WSGI_APPLICATION = 'school_management.wsgi.application'

# Database
IS_VERCEL = "VERCEL" in os.environ

# Check for various Vercel-specific environment variables
# POSTGRES_URL is often pooled, POSTGRES_URL_NON_POOLING is direct
db_url = (
    os.environ.get('POSTGRES_URL_NON_POOLING') or 
    os.environ.get('POSTGRES_URL') or 
    os.environ.get('DATABASE_URL') or
    os.environ.get('POSTGRES_PRISMA_URL')
)

if db_url:
    DATABASES = {
        'default': dj_database_url.parse(db_url, conn_max_age=600, conn_health_checks=True)
    }
else:
    # If no URL, try individual parts if they exist (Vercel sometimes provides these)
    if all(k in os.environ for k in ['POSTGRES_DB', 'POSTGRES_USER', 'POSTGRES_PASSWORD', 'POSTGRES_HOST']):
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': os.environ.get('POSTGRES_DB'),
                'USER': os.environ.get('POSTGRES_USER'),
                'PASSWORD': os.environ.get('POSTGRES_PASSWORD'),
                'HOST': os.environ.get('POSTGRES_HOST'),
                'PORT': os.environ.get('POSTGRES_PORT', '5432'),
            }
        }
    else:
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': BASE_DIR / 'db.sqlite3',
            }
        }

# Safety check for Vercel deployment
if IS_VERCEL and DATABASES['default']['ENGINE'] == 'django.db.backends.sqlite3':
    # Diagnostic info
    v_env = os.environ.get('VERCEL_ENV', 'unknown')
    v_branch = os.environ.get('VERCEL_GIT_COMMIT_REF', 'unknown')
    
    # Let's see ALL keys that are NOT internal Vercel/System ones to find if user mistyped something
    all_keys = sorted(os.environ.keys())
    user_keys = [k for k in all_keys if not k.startswith(('VERCEL_', 'AWS_', 'LAMBDA_', '_', 'PATH', 'PWD', 'HOME', 'LANG'))]
    vercel_keys = [k for k in all_keys if k.startswith('VERCEL_')]
    
    print(f"DIAGNOSTIC - Env: {v_env}, Branch: {v_branch}")
    print(f"DIAGNOSTIC - User defined/Integration keys: {user_keys}")
    print(f"DIAGNOSTIC - Vercel keys: {vercel_keys}")
    
    # Allow build-time commands to pass (e.g., collectstatic)
    BUILD_COMMANDS = ['collectstatic', 'generate']
    if not any(cmd in sys.argv for cmd in BUILD_COMMANDS):
        from django.core.exceptions import ImproperlyConfigured
        error_msg = (
            f"Vercel Deployment Error: No database variables found.\n"
            f"Current Vercel Environment: {v_env}\n"
            f"Current Branch: {v_branch}\n"
            f"Non-system keys found: {user_keys}\n\n"
            "CRITICAL: We did NOT find 'POSTGRES_URL' or 'DATABASE_URL' in your environment.\n"
            "Please check your Vercel Project Settings -> Environment Variables.\n"
            "If they are missing there, you MUST manually add 'POSTGRES_URL' as a variable."
        )
        raise ImproperlyConfigured(error_msg)





# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles_build', 'static')

# Media files (Uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Session settings
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 86400  # 24 hours
