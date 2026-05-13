from django.contrib import admin
from django.db import models
from django.http import HttpRequest

from salute.core.admin import BaseModelAdminMixin
from salute.core.models import BaseModel
from salute.integrations.tsa.admin import TSAObjectModelAdminMixin
from salute.integrations.tsa.models import TSATimestampedObject
from salute.mailing_groups.models import SystemMailingGroupMembership
from salute.people.models import (
    Permit,
    PermitActivity,
    PermitActivityGroup,
    PermitCategory,
    PermitStatus,
    PermitType,
    Person,
)
from salute.roles.models import Accreditation, Role


class PersonRoleInlineAdmin(admin.TabularInline):
    model = Role
    readonly_fields = Role.TSA_FIELDS


class PersonAccreditationInlineAdmin(admin.TabularInline):
    model = Accreditation
    readonly_fields = Accreditation.TSA_FIELDS


class SystemMailingGroupMembershipInline(admin.TabularInline):
    model = SystemMailingGroupMembership
    extra = 0
    verbose_name = "Mailing Group"
    hide_title = True
    classes = ["collapse"]

    def has_change_permission(self, request: HttpRequest, obj: models.Model | None = None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj: models.Model | None = None) -> bool:
        return False

    def has_add_permission(self, request: HttpRequest, obj: models.Model | None = None) -> bool:
        return False


@admin.register(Person)
class PersonAdmin(TSAObjectModelAdminMixin, admin.ModelAdmin):
    list_display = (
        "__str__",
        "first_name",
        "last_name",
        "membership_number",
        "is_suspended",
    )
    list_filter = ("is_suspended", ("workspace_account", admin.EmptyFieldListFilter))
    search_fields = ("display_name", "membership_number", "tsa_id")
    inlines = (PersonRoleInlineAdmin, PersonAccreditationInlineAdmin, SystemMailingGroupMembershipInline)

    fieldsets = (
        (None, {"fields": ("first_name", "last_name", "formatted_membership_number", "is_suspended")}),
        (
            "Contact Info",
            {
                "fields": (
                    "workspace_account",
                    "contact_email",
                    "phone_number",
                    "alternate_phone_number",
                ),
            },
        ),
        (
            "Email Addresses",
            {
                "classes": ("collapse",),
                "fields": (
                    "tsa_email",
                    "default_email",
                    "alternate_email",
                ),
            },
        ),
    ) + TSAObjectModelAdminMixin.FIELDSETS

    def get_readonly_fields(self, request: HttpRequest, obj: TSATimestampedObject | None = None) -> list[str]:  # type: ignore[override]
        return super().get_readonly_fields(request, obj) + ["contact_email", "workspace_account"]


@admin.register(PermitActivityGroup)
class PermitActivityGroupAdmin(BaseModelAdminMixin, admin.ModelAdmin):
    list_display = ("name", "mailing_slug")
    search_fields = ("name", "mailing_slug")

    fieldsets = ((None, {"fields": ("name", "mailing_slug")}),) + BaseModelAdminMixin.FIELDSETS

    def has_change_permission(self, request: HttpRequest, obj: models.Model | None = None) -> bool:
        return request.user.is_superuser

    def has_add_permission(self, request: HttpRequest, obj: models.Model | None = None) -> bool:
        return request.user.is_superuser


@admin.register(PermitActivity)
class PermitActivityAdmin(BaseModelAdminMixin, admin.ModelAdmin):
    list_display = ("name", "group")
    list_filter = ("group",)
    search_fields = ("name", "group__name")

    fieldsets = ((None, {"fields": ("name", "group")}),) + BaseModelAdminMixin.FIELDSETS

    def get_readonly_fields(self, request: HttpRequest, obj: BaseModel | None = None) -> list[str]:
        return super().get_readonly_fields(request, obj) + ["name"]

    def has_change_permission(self, request: HttpRequest, obj: models.Model | None = None) -> bool:
        return request.user.is_superuser


@admin.register(PermitCategory)
class PermitCategoryAdmin(BaseModelAdminMixin, admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)

    fieldsets = ((None, {"fields": ("name",)}),) + BaseModelAdminMixin.FIELDSETS


@admin.register(PermitType)
class PermitTypeAdmin(BaseModelAdminMixin, admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)

    fieldsets = ((None, {"fields": ("name",)}),) + BaseModelAdminMixin.FIELDSETS


@admin.register(PermitStatus)
class PermitStatusAdmin(BaseModelAdminMixin, admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)

    fieldsets = ((None, {"fields": ("name",)}),) + BaseModelAdminMixin.FIELDSETS


@admin.register(Permit)
class PermitAdmin(BaseModelAdminMixin, admin.ModelAdmin):
    list_display = ("person", "activity", "category", "type", "status", "start_date", "granted_on", "expiry_date")
    list_filter = ("activity", "category", "type", "status")
    search_fields = (
        "person__display_name",
        "person__membership_number",
        "activity__name",
        "category__name",
        "type__name",
    )

    fieldsets = (
        (
            None,
            {"fields": ("person", "activity", "category", "type", "status", "start_date")},
        ),
        ("Details", {"fields": ("assessor_name", "restriction_details")}),
        ("Dates", {"fields": ("date_of_permit_application", "granted_on", "expiry_date")}),
    ) + BaseModelAdminMixin.FIELDSETS
