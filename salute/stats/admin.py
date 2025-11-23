from django.contrib import admin

from salute.stats.models import (
    DistrictSummaryRecord,
    GroupSummaryRecord,
    SectionCensusReturn,
    SectionSummaryRecord,
    TeamSummaryRecord,
)


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


@admin.register(TeamSummaryRecord)
class TeamSummaryRecordAdmin(admin.ModelAdmin):
    list_display = ("team", "date", "total_people")
    list_filter = ("team__team_type", "date")
    search_fields = ("team__name",)
    ordering = ("-date",)


@admin.register(SectionSummaryRecord)
class SectionSummaryRecordAdmin(admin.ModelAdmin):
    list_display = ("section", "date", "total_people")
    list_filter = ("section__section_type", "date")
    search_fields = ("section__shortcode", "section__unit_name")
    ordering = ("-date",)


@admin.register(GroupSummaryRecord)
class GroupSummaryRecordAdmin(admin.ModelAdmin):
    list_display = ("group", "date", "total_people", "total_people_with_sub_units")
    list_filter = ("group__group_type", "date")
    search_fields = ("group__shortcode", "group__unit_name")
    ordering = ("-date",)


@admin.register(DistrictSummaryRecord)
class DistrictSummaryRecordAdmin(admin.ModelAdmin):
    list_display = ("district", "date", "total_people", "total_people_with_sub_units")
    list_filter = ("date",)
    search_fields = ("district__shortcode", "district__unit_name")
    ordering = ("-date",)
