"""
Django settings for CENTRAL_LOGIN_SYSTEM project.
"""

from pathlib import Path
import os
from dotenv import load_dotenv

# -------------------- Paths --------------------
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv() 

# -------------------- Core ---------------------
SECRET_KEY = 'django-insecure-c_%uwi0@g9fzwpollp#n1i3q-a=h+_4c(!z51fnj1ljm(zyg$$'
DEBUG = True
ALLOWED_HOSTS: list[str] = ['activate.imcbs.com','www.activate.imcbs.com',"*"]

# -------------------- Apps ---------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    "app1",
    "WebApp",
    "MobileApp",
    "storages",  # for Cloudflare R2 (S3-compatible)
    'branch',
    'StoreShop',
    'ModuleAndPackage',
    'user_controll',
    'client_id_list'
]

# ------------------------------------------------------------------
# Cloudflare R2 (S3-compatible) – controlled by CLOUDFLARE_R2_ENABLED
# ------------------------------------------------------------------
CLOUDFLARE_R2_ENABLED = os.getenv("CLOUDFLARE_R2_ENABLED", "false").lower() == "true"

if CLOUDFLARE_R2_ENABLED:
    # Django 4.2+ uses STORAGES dict instead of DEFAULT_FILE_STORAGE
    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
            "OPTIONS": {
                "access_key": os.getenv("CLOUDFLARE_R2_ACCESS_KEY"),
                "secret_key": os.getenv("CLOUDFLARE_R2_SECRET_KEY"),
                "bucket_name": os.getenv("CLOUDFLARE_R2_BUCKET"),
                "endpoint_url": os.getenv("CLOUDFLARE_R2_BUCKET_ENDPOINT"),
                "region_name": "auto",
                "signature_version": "s3v4",
                "file_overwrite": False,
                "default_acl": None,
                "querystring_auth": False,
                "custom_domain": os.getenv("CLOUDFLARE_R2_PUBLIC_URL", "").replace("https://", "").replace("http://", ""),
            },
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }
    
    # Public-facing base URL for user-uploaded media
    MEDIA_URL = os.getenv("CLOUDFLARE_R2_PUBLIC_URL", "").rstrip("/") + "/"

else:
    # Fall back to local disk storage
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }
    MEDIA_ROOT = BASE_DIR / "media"
    MEDIA_URL = "/media/"

# -------------------- Middleware ----------------
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'app1.middleware.MenuPermissionMiddleware',
]

# -------------------- URLs / Templates ----------
ROOT_URLCONF = 'CENTRAL_LOGIN_SYSTEM.urls'

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "app1" / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = 'CENTRAL_LOGIN_SYSTEM.wsgi.application'

# -------------------- Database ------------------
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'central_login_system',  # Your DB name
        'USER': 'postgres',           # Your DB username
        'PASSWORD': 'info@imc',   # Your DB password
        'HOST': 'localhost',          # Or server IP if remote
        'PORT': '5432',               # Default PostgreSQL port
    }
}




LOGIN_URL = "/login/"

# -------------------- Auth ----------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# -------------------- I18N / TZ -----------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# -------------------- Static --------------------
STATIC_URL = 'static/'

# -------------------- Defaults ------------------
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
