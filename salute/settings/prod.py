# type: ignore
from .base import *  # noqa: F403

SECRET_KEY = ""
ALLOWED_HOSTS: list[str] = []

# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",  # noqa: F405
    }
}

# Auth0 Settings
AUTH0_DOMAIN = ""
AUTH0_AUDIENCE = "example.com"
AUTH0_JWKS_CACHE_TIMEOUT = 600
