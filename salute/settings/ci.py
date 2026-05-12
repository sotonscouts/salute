# type: ignore
"""Django settings for automated tests (e.g. GitHub Actions).

The Postgres service maps host port **5432**; local ``dev`` settings use **5433**
for Docker Compose. Import everything from ``dev`` then override the DB port only.
"""

from .dev import *  # noqa: F403

DATABASES["default"]["PORT"] = "5432"  # noqa: F405
