from django.contrib import admin
from django.http import HttpRequest

from salute.core.models import BaseModel
from salute.hierarchy.constants import DISTRICT_SECTION_TYPES
from salute.hierarchy.models import District, Group, Section
from salute.integrations.tsa.admin import TSATimestampedObjectModelAdminMixin


@admin.register(District)
class DistrictAdmin(TSATimestampedObjectModelAdminMixin, admin.ModelAdmin):
    list_display = ("unit_name",)
    search_fields = ("unit_name", "tsa_id")

    fieldsets = ((None, {"fields": ("unit_name", "shortcode")}),) + TSATimestampedObjectModelAdminMixin.FIELDSETS


@admin.register(Group)
class GroupAdmin(TSATimestampedObjectModelAdminMixin, admin.ModelAdmin):
    list_display = (
        "display_name",
        "ordinal",
        "location_name",
        "district",
        "group_type",
    )
    list_filter = ("group_type",)
    search_fields = ("unit_name", "tsa_id", "location_name")

    fieldsets = (
        (None, {"fields": ("display_name", "shortcode", "district")}),
        (
            "Group",
            {
                "fields": (
                    "unit_name",
                    "location_name",
                    "ordinal",
                    "local_unit_number",
                    "group_type",
                    "charity_number",
                )
            },
        ),
    ) + TSATimestampedObjectModelAdminMixin.FIELDSETS

    def get_readonly_fields(self, request: HttpRequest, obj: BaseModel | None = None) -> list[str]:
        return super().get_readonly_fields(request, obj) + [  # type: ignore[arg-type]
            "ordinal",
            "display_name",
        ]

    def has_change_permission(self, request: HttpRequest, obj: BaseModel | None = None) -> bool:
        return request.user.is_superuser


@admin.register(Section)
class SectionAdmin(TSATimestampedObjectModelAdminMixin, admin.ModelAdmin):
    list_display = ("display_name", "section_type", "group", "district")
    list_filter = ("section_type", "group", "usual_weekday")
    search_fields = ("unit_name", "tsa_id")

    fieldsets = (
        (None, {"fields": ("display_name", "shortcode", "district", "group")}),
        ("Section", {"fields": ("unit_name", "section_type", "nickname", "mailing_slug", "usual_weekday")}),
    ) + TSATimestampedObjectModelAdminMixin.FIELDSETS

    def get_readonly_fields(self, request: HttpRequest, obj: Section | None = None) -> list[str]:  # type: ignore[override]
        extra_readonly_fields = ["display_name"]

        # Mailing slugs are only applicable to district sections
        if obj is not None and obj.section_type not in DISTRICT_SECTION_TYPES:
            extra_readonly_fields.append("mailing_slug")

        return super().get_readonly_fields(request, obj) + extra_readonly_fields

    def has_change_permission(self, request: HttpRequest, obj: BaseModel | None = None) -> bool:
        return request.user.is_superuser
