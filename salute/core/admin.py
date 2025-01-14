from django.http import HttpRequest

from salute.core.models import BaseModel


class BaseModelAdminMixin:
    FIELDSETS = (
        (
            "IDs",
            {
                "fields": (
                    "id",
                )
            },
        ),
        (
            "Dates",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    def get_readonly_fields(self, request: HttpRequest, obj: BaseModel | None = None) -> tuple[str, ...]:
        assert obj is not None
        return (
            "id",
            "created_at",
            "updated_at",
        ) + obj.TSA_FIELDS

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj: BaseModel | None = None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj: BaseModel | None = None) -> bool:
        return False
