# type: ignore
from environ import Env

from .base import *  # noqa: F403

env = Env()

SECRET_KEY = env("SECRET_KEY", str)
ALLOWED_HOSTS: list[str] = [env("ALLOWED_HOST", str)]

# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("SQL_DATABASE", str),
        "USER": env("SQL_USER", str),
        "PASSWORD": env("SQL_PASSWORD", str),
        "HOST": env("SQL_HOST", str),
        "PORT": env("SQL_PORT", int, default=5432),
    }
}
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# Auth0 Settings
AUTH0_DOMAIN = env("AUTH0_DOMAIN", str)
AUTH0_AUDIENCE = env("AUTH0_AUDIENCE", str)
AUTH0_JWKS_CACHE_TIMEOUT = env("AUTH0_JWKS_CACHE_TIMEOUT", int, default=600)
