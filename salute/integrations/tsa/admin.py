from typing import Any

from django.http import HttpRequest

from salute.core.admin import BaseModelAdminMixin
from salute.integrations.tsa.models import TSAObject, TSATimestampedObject


class TSATimestampedObjectModelAdminMixin(BaseModelAdminMixin):
    FIELDSETS: Any = (
        (
            "IDs",
            {
                "fields": (
                    "id",
                    "tsa_id",
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

    def get_readonly_fields(self, request: HttpRequest, obj: TSATimestampedObject | None = None) -> list[str]:  # type: ignore[override]
        assert obj is not None
        return [
            "id",
            "tsa_id",
            "shortcode",
            "created_at",
            "updated_at",
            "tsa_last_modified",
        ] + list(obj.TSA_FIELDS)


class TSAObjectModelAdminMixin(BaseModelAdminMixin):
    FIELDSETS: Any = (
        (
            "IDs",
            {
                "fields": (
                    "id",
                    "tsa_id",
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

    def get_readonly_fields(self, request: HttpRequest, obj: TSAObject | None = None) -> list[str]:  # type: ignore[override]
        assert obj is not None
        return [
            "id",
            "tsa_id",
            "created_at",
            "updated_at",
        ] + list(obj.TSA_FIELDS)
