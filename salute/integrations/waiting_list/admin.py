from typing import Any

from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.db.models import QuerySet
from django.http import HttpRequest
from django.utils import timezone

from salute.core.admin import BaseModelAdminMixin
from salute.hierarchy.constants import SectionType
from salute.integrations.waiting_list.models import (
    TargetSection,
    WaitingListEntry,
    WaitingListSectionRecord,
    WaitingListSectionTypeRecord,
    WaitingListUnit,
)


@admin.register(WaitingListUnit)
class WaitingListUnitAdmin(BaseModelAdminMixin, admin.ModelAdmin):
    list_display = ("name", "group", "section")
    list_filter = ("group", "section")
    search_fields = ("name", "group__name", "section__name")

    def get_fieldsets(  # type: ignore[override]
        self, request: HttpRequest, obj: WaitingListUnit | None = None
    ) -> list[tuple[str, dict[str, Any]]]:
        return (
            (
                "Details",
                {"fields": ("name", "group", "section")},
            ),
        ) + BaseModelAdminMixin.FIELDSETS

    def get_readonly_fields(self, request: HttpRequest, obj: WaitingListUnit | None = None) -> list[str]:  # type: ignore[override]
        return super().get_readonly_fields(request, obj) + ["name"]

    def has_change_permission(self, request: HttpRequest, obj: WaitingListUnit | None = None) -> bool:  # type: ignore[override]
        return request.user.is_superuser


class TargetSectionFilter(SimpleListFilter):
    title = "target section"
    parameter_name = "target_section"

    def lookups(self, request: HttpRequest, model_admin: admin.ModelAdmin) -> list[tuple[str, str]]:
        """Return list of tuples (value, human-readable label)."""
        choices = []
        # Add all section types
        for section_type in SectionType:
            choices.append((section_type.value, section_type.label))
        # Add TOO_YOUNG and TOO_OLD
        choices.append((TargetSection.TOO_YOUNG.value, TargetSection.TOO_YOUNG.label))
        choices.append((TargetSection.TOO_OLD.value, TargetSection.TOO_OLD.label))
        return choices

    def queryset(self, request: HttpRequest, queryset: QuerySet[WaitingListEntry]) -> QuerySet[WaitingListEntry]:
        """Filter the queryset based on the selected value."""
        if self.value():
            return queryset.filter(target_section=self.value())  # type: ignore[misc]
        return queryset


@admin.register(WaitingListEntry)
class WaitingListEntryAdmin(BaseModelAdminMixin, admin.ModelAdmin):
    list_display = (
        "external_id",
        "date_of_birth",
        "postcode",
        "age",
        "target_section",
        "joined_waiting_list_at",
        "successfully_transferred",
    )
    list_filter = ("successfully_transferred", "units", TargetSectionFilter)
    search_fields = ("external_id", "postcode")
    readonly_fields = ("units", "age", "target_section", "created_at", "updated_at")
    filter_horizontal = ("units",)

    def get_readonly_fields(self, request: HttpRequest, obj: WaitingListEntry | None = None) -> list[str]:  # type: ignore[override]
        return super().get_readonly_fields(request, obj) + ["age", "target_section"]

    @admin.display(description="Age")
    def age(self, obj: WaitingListEntry) -> str:
        """Display the age calculated from the queryset annotation."""
        if hasattr(obj, "age") and obj.age is not None:
            # obj.age is a timedelta, extract years
            total_days = obj.age.days
            years = total_days // 365
            return f"{years} years"
        return "-"

    @admin.display(description="Target Section")
    def target_section(self, obj: WaitingListEntry) -> str:
        """Display the target section based on age."""
        if hasattr(obj, "target_section") and obj.target_section:
            # Try to match to SectionType first
            for section_type in SectionType:
                if obj.target_section == section_type.value:
                    return section_type.label
            # Check for TOO_YOUNG/TOO_OLD
            if obj.target_section == TargetSection.TOO_YOUNG.value:
                return TargetSection.TOO_YOUNG.label
            if obj.target_section == TargetSection.TOO_OLD.value:
                return TargetSection.TOO_OLD.label
            return obj.target_section
        return "-"

    def get_queryset(self, request: HttpRequest) -> QuerySet[WaitingListEntry]:
        return super().get_queryset(request).with_age(timezone.now()).with_target_section(timezone.now())  # type: ignore[attr-defined]


@admin.register(WaitingListSectionRecord)
class WaitingListSectionRecordAdmin(BaseModelAdminMixin, admin.ModelAdmin):
    list_display = ("section", "date", "waiting_list_count")
    list_filter = ("date", "section__group", "section__section_type")
    search_fields = ("section__shortcode", "section__unit_name")
    ordering = ("-date",)
    readonly_fields = ("section", "date", "waiting_list_count")


@admin.register(WaitingListSectionTypeRecord)
class WaitingListSectionTypeRecordAdmin(BaseModelAdminMixin, admin.ModelAdmin):
    list_display = ("section_type", "date", "waiting_list_count")
    list_filter = ("date", "section_type")
    search_fields = ("section_type",)
    ordering = ("-date",)
    readonly_fields = ("section_type", "date", "waiting_list_count")
