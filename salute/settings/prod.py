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
