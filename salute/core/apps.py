from typing import Any

from django.apps import AppConfig
from django.db.backends.base.base import BaseDatabaseWrapper
from psycopg.types.range import RangeInfo, register_range


def on_connection_created(sender: Any, connection: BaseDatabaseWrapper, **kwargs: Any) -> None:
    if connection.vendor == "postgresql":
        try:
            info = RangeInfo.fetch(connection.connection, "timerange")
            register_range(info, connection.connection)
        except Exception:  # noqa: BLE001, S110
            # The type might not exist yet (e.g. during migrations)
            pass


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "salute.core"

    def ready(self) -> None:
        from django.db.backends.signals import connection_created

        from . import permissions  # noqa: F401

        connection_created.connect(on_connection_created)
