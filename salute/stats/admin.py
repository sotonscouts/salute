from django.contrib import admin

from salute.stats.models import SectionCensusReturn


@admin.register(SectionCensusReturn)
class SectionCensusReturnAdmin(admin.ModelAdmin):
    list_display = (
        "section",
        "year",
        "data_format_version",
        "annual_subs_cost",
        "total_volunteers",
        "total_young_people",
        "ratio_young_people_to_volunteers",
    )
    list_filter = ("section__section_type", "section__group", "year", "data_format_version")
    search_fields = ("section__shortcode", "section__unit_name")
    ordering = ("-year",)
