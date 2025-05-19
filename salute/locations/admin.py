from django.contrib import admin

from .models import Site, SiteOperator


@admin.register(SiteOperator)
class SiteOperatorAdmin(admin.ModelAdmin):
    list_display = ("display_name", "operator_type")
    list_filter = ("district", "group")
    search_fields = ("name", "district__unit_name", "group__unit_name")
    readonly_fields = ("display_name",)

    @admin.display(description="Type")
    def operator_type(self, obj: SiteOperator) -> str:
        if obj.district:
            return "District"
        if obj.group:
            return "Group"
        return "Third Party"


@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):
    list_display = ("name", "tenure_type", "operator", "town", "postcode")
    list_filter = ("tenure_type", "operator")
    search_fields = ("name", "building_name", "street", "town", "postcode")

    fieldsets = (
        (
            None,
            {
                "fields": ("name", "tenure_type", "operator"),
            },
        ),
        (
            "Address",
            {
                "fields": (
                    "building_name",
                    "street_number",
                    "street",
                    "town",
                    "county",
                    "postcode",
                    "uprn",
                ),
            },
        ),
        (
            "Location",
            {
                "fields": (
                    "latitude",
                    "longitude",
                ),
            },
        ),
    )
