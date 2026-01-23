# type: ignore
import sentry_sdk
from environ import Env
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.strawberry import StrawberryIntegration

from .base import *  # noqa: F403

env = Env()

SECRET_KEY = env("SECRET_KEY", str)
ALLOWED_HOSTS: list[str] = [env("ALLOWED_HOST", str)]

CSRF_TRUSTED_ORIGINS = [env("CSRF_TRUSTED_ORIGIN", str)]
CORS_ALLOWED_ORIGINS = [env("CORS_ALLOWED_ORIGIN", str)]

# Sentry Configuration
sentry_sdk.init(
    dsn=env("SENTRY_DSN", str, default=""),
    integrations=[
        DjangoIntegration(),
        StrawberryIntegration(async_execution=True),
    ],
    send_default_pii=env("SENTRY_SEND_DEFAULT_PII", bool, default=False),
    environment=env("SENTRY_ENVIRONMENT", str, default="production"),
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    traces_sample_rate=env("SENTRY_TRACES_SAMPLE_RATE", float, default=0.1),
    # Set profiles_sample_rate to 1.0 to profile 100%
    # of sampled transactions.
    # We recommend adjusting this value in production.
    profiles_sample_rate=env("SENTRY_PROFILES_SAMPLE_RATE", float, default=0.1),
)

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

BIRDBATH_REQUIRED = False

# Auth0 Settings
AUTH0_DOMAIN = env("AUTH0_DOMAIN", str)
AUTH0_AUDIENCE = env("AUTH0_AUDIENCE", str)
AUTH0_JWKS_CACHE_TIMEOUT = env("AUTH0_JWKS_CACHE_TIMEOUT", int, default=600)

# Replace with a link to the TSA person profile. Use $tsaid to replace with the TSA ID.
# This is used in the TSA person profile link in the API.
TSA_PERSON_PROFILE_LINK_TEMPLATE = env(
    "TSA_PERSON_PROFILE_LINK_TEMPLATE",
    str,
    default="https://example.com/people/$tsaid/",
)

TSA_UNIT_LINK_TEMPLATE = env(
    "TSA_UNIT_LINK_TEMPLATE",
    str,
    default="https://example.com/units/$tsaid/details/",
)

TSA_TEAM_LINK_TEMPLATE = env(
    "TSA_TEAM_LINK_TEMPLATE",
    str,
    default="https://example.com/teams/$unitid/$teamtypeid/details/",
)

OSM_CLIENT_ID = env("OSM_CLIENT_ID", str)
OSM_CLIENT_SECRET = env("OSM_CLIENT_SECRET", str)
OSM_DISTRICT_SECTION_ID = env("OSM_DISTRICT_SECTION_ID", str)

GOOGLE_DOMAIN = env("GOOGLE_DOMAIN", str)

AIRTABLE_API_KEY = env("AIRTABLE_API_KEY", str)
AIRTABLE_BASE_ID = env("AIRTABLE_BASE_ID", str)
AIRTABLE_TABLE_ID = env("AIRTABLE_TABLE_ID", str)
