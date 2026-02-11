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
    relevant_keys = [k for k in os.environ.keys() if any(x in k for x in ['POSTGRES', 'DATABASE', 'URL', 'VERCEL'])]
    
    print(f"DIAGNOSTIC - Environment: {v_env}, Branch: {v_branch}")
    print(f"DIAGNOSTIC - Available environment keys: {relevant_keys}")
    
    # Allow build-time commands to pass (e.g., collectstatic)
    BUILD_COMMANDS = ['collectstatic', 'generate']
    if not any(cmd in sys.argv for cmd in BUILD_COMMANDS):
        from django.core.exceptions import ImproperlyConfigured
        error_msg = (
            f"Vercel Deployment Error: Missing hosted database configuration.\n"
            f"Current Vercel Environment: {v_env}\n"
            f"Current Branch: {v_branch}\n"
            "SQLite is not supported on Vercel's read-only filesystem.\n\n"
            "This usually happens because your database is only connected to the 'Production' environment.\n"
            "Please follow these steps:\n"
            "1. Go to your project on the Vercel Dashboard.\n"
            "2. Navigate to the 'Storage' tab and click on your Postgres database.\n"
            "3. Click 'Connect' (or 'Manage' -> 'Connect') and ensure 'Preview' is checked.\n"
            "4. Alternatively, go to 'Settings' -> 'Environment Variables' and ensure 'DATABASE_URL' is enabled for 'Preview' and 'Production'.\n"
            "5. Redeploy your project."
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
