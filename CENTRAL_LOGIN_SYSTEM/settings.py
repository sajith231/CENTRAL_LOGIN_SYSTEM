"""
Django settings for CENTRAL_LOGIN_SYSTEM project.
"""

from pathlib import Path
import os
from dotenv import load_dotenv

# -------------------- Paths --------------------
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv()  # <-- ensure .env is loaded

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
]

# -------------------- Media (defaults: local) ---
# These are used when R2 is disabled


# -------------------- Cloudflare R2 -------------
CLOUDFLARE_R2_ENABLED = os.getenv("CLOUDFLARE_R2_ENABLED", "false").lower() == "true"

if CLOUDFLARE_R2_ENABLED:
    DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"

    AWS_ACCESS_KEY_ID = os.getenv("CLOUDFLARE_R2_ACCESS_KEY")
    AWS_SECRET_ACCESS_KEY = os.getenv("CLOUDFLARE_R2_SECRET_KEY")
    AWS_STORAGE_BUCKET_NAME = os.getenv("CLOUDFLARE_R2_BUCKET")
    AWS_S3_ENDPOINT_URL = os.getenv("CLOUDFLARE_R2_BUCKET_ENDPOINT")
    AWS_S3_REGION_NAME = "auto"
    AWS_S3_SIGNATURE_VERSION = "s3v4"
    AWS_S3_FILE_OVERWRITE = False
    AWS_DEFAULT_ACL = None
    AWS_QUERYSTRING_AUTH = False

    # PUBLIC R2 URL — must end with /
    MEDIA_URL = os.getenv("CLOUDFLARE_R2_PUBLIC_URL").rstrip("/") + "/"

else:
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
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'newdb.sqlite3',
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
