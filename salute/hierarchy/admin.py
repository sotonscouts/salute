from django.contrib import admin
from django.http import HttpRequest

from salute.core.models import BaseModel
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
        "unit_name",
        "local_unit_number",
        "location_name",
        "district",
        "group_type",
    )
    list_filter = ("group_type",)
    search_fields = ("unit_name", "tsa_id", "location_name")

    fieldsets = (
        (None, {"fields": ("unit_name", "shortcode", "district")}),
        (
            "Group",
            {
                "fields": (
                    "location_name",
                    "local_unit_number",
                    "group_type",
                    "charity_number",
                )
            },
        ),
    ) + TSATimestampedObjectModelAdminMixin.FIELDSETS

    def get_readonly_fields(self, request: HttpRequest, obj: BaseModel | None = None) -> list[str]:
        return super().get_readonly_fields(request, obj) + [  # type: ignore[arg-type]
            "local_unit_number",
            "location_name",
        ]


@admin.register(Section)
class SectionAdmin(TSATimestampedObjectModelAdminMixin, admin.ModelAdmin):
    list_display = ("unit_name", "section_type", "group", "district")
    list_filter = ("section_type", "group")
    search_fields = ("unit_name", "tsa_id")

    fieldsets = (
        (None, {"fields": ("unit_name", "shortcode", "district", "group")}),
        ("Section", {"fields": ("section_type",)}),
    ) + TSATimestampedObjectModelAdminMixin.FIELDSETS
