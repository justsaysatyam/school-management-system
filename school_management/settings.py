"""
Django settings for school_management project.
Mid Point School - School Management System
"""

from pathlib import Path
import os
import sys
# Import dj_database_url conditionally is better for local dev if not installed
try:
    import dj_database_url
except ImportError:
    dj_database_url = None


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

if db_url and dj_database_url:
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
if IS_VERCEL:
    # Diagnostic info
    v_env = os.environ.get('VERCEL_ENV', 'unknown')
    v_branch = os.environ.get('VERCEL_GIT_COMMIT_REF', 'unknown')
    
    # Check for a dummy test variable to see if integration is working at all
    foo_test = os.environ.get('FOO', 'NOT FOUND')
    
    # Diagnostic logging
    print(f"DIAGNOSTIC - Env: {v_env}, Branch: {v_branch}")
    print(f"DIAGNOSTIC - FOO test: {foo_test}")
    
    # Allow build-time commands to pass (e.g., collectstatic)
    # We force an in-memory database during build so Django doesn't fail on connection checks
    IS_BUILDING = any(cmd in sys.argv for cmd in ['collectstatic', 'generate', 'makemigrations', 'migrate']) or os.environ.get('CI') == '1'
    
    if IS_BUILDING:
        print("DIAGNOSTIC - Build phase detected. Using in-memory database.")
        DATABASES['default'] = {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    elif DATABASES['default']['ENGINE'] == 'django.db.backends.sqlite3' and v_env != 'unknown':
        from django.core.exceptions import ImproperlyConfigured
        
        # More diagnostics before raising
        db_candidate_keys = [k for k in os.environ.keys() if 'POSTGRES' in k.upper() or 'DATABASE' in k.upper()]
        user_keys = [k for k in os.environ.keys() if not k.startswith(('VERCEL_', 'AWS_', 'LAMBDA_', '_', 'PATH', 'PWD', 'HOME', 'LANG'))]
        
        error_msg = (
            f"Vercel Deployment Error: No database variables found.\n"
            f"Current Vercel Environment: {v_env}\n"
            f"FOO Test Variable: {foo_test}\n"
            f"Potential DB Keys Found: {db_candidate_keys}\n\n"
            "Vercel modern platform detected but no database variable injected.\n"
            "Please go to your Vercel Project -> Settings -> Environment Variables and manually add:\n"
            "1. Key: DATABASE_URL, Value: (Your Postgres URL from Storage tab)\n"
            "Ensure 'Production' and 'Preview' are both checked."
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
