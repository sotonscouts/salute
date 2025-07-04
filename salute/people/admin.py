from django.contrib import admin
from django.db import models
from django.http import HttpRequest

from salute.integrations.tsa.admin import TSAObjectModelAdminMixin
from salute.integrations.tsa.models import TSATimestampedObject
from salute.mailing_groups.models import SystemMailingGroupMembership
from salute.people.models import Person
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
                    "primary_email",
                    "default_email",
                    "alternate_email",
                ),
            },
        ),
    ) + TSAObjectModelAdminMixin.FIELDSETS

    def get_readonly_fields(self, request: HttpRequest, obj: TSATimestampedObject | None = None) -> list[str]:  # type: ignore[override]
        return super().get_readonly_fields(request, obj) + ["contact_email", "workspace_account"]
