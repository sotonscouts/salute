from django.http import HttpRequest

from salute.integrations.tsa.models import TSAObject


class TSAObjectModelAdminMixin:

    FIELDSETS = (
        (
            "IDs",
            {
                "fields": (
                    "id",
                    "tsa_id",
                    "shortcode",
                )
            },
        ),
        (
            "Dates",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                    "tsa_last_modified",
                )
            },
        ),
    )

    def get_readonly_fields(self, request: HttpRequest, obj: TSAObject | None =None) -> tuple[str, ...]:
        return (
            "id",
            "tsa_id",
            "shortcode",
            "created_at",
            "updated_at",
            "tsa_last_modified",
        ) + obj.TSA_FIELDS

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj: TSAObject | None = None) -> bool:
        return False
