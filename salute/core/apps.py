from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "salute.core"

    def ready(self) -> None:
        from . import permissions  # noqa: F401
