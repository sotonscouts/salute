# type: ignore
from .base import *  # noqa: F403

ALLOWED_HOSTS: list[str] = ["*"]

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-)r&0lm8c%w6x%5tk9k73pepp+!-pkr%e$8&)r(n1k&mo(dv7@3"  # noqa: S105

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# SECURITY WARNING: Do not allow unauthenticated GraphiQL in production
# This setting also disables query introspection
ALLOW_UNAUTHENTICATED_GRAPHIQL = True

# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",  # noqa: F405
    }
}

if DEBUG:
    INSTALLED_APPS.append("debug_toolbar")  # noqa: F405

    # If debug is enabled, then turn on debug toolbar and allow the local machine to use it
    MIDDLEWARE = ["strawberry_django.middlewares.debug_toolbar.DebugToolbarMiddleware"] + MIDDLEWARE  # noqa: F405
    INTERNAL_IPS = ["127.0.0.1"]

CORS_ALLOW_ALL_ORIGINS = True
