from django.contrib import admin
from django.http import HttpRequest

from salute.integrations.tsa.admin import TSAObjectModelAdminMixin
from salute.integrations.tsa.models import TSATimestampedObject
from salute.people.models import Person


@admin.register(Person)
class PersonAdmin(TSAObjectModelAdminMixin, admin.ModelAdmin):
    list_display = (
        "__str__",
        "first_name",
        "last_name",
        "membership_number",
        "is_suspended",
    )
    list_filter = ("is_suspended",)
    search_fields = ("display_name", "membership_number", "tsa_id")

    fieldsets = (
        (None, {"fields": ("first_name", "last_name", "formatted_membership_number", "is_suspended")}),
        (
            "Contact Info",
            {
                "fields": (
                    "tsa_email",
                    "primary_email",
                    "default_email",
                    "alternate_email",
                    "phone_number",
                ),
            },
        ),
    ) + TSAObjectModelAdminMixin.FIELDSETS

    def get_readonly_fields(self, request: HttpRequest, obj: TSATimestampedObject | None = None) -> list[str]:  # type: ignore[override]
        return super().get_readonly_fields(request, obj) + ["contact_email"]
