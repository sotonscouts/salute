from django.contrib import admin

from salute.core.admin import BaseModelAdminMixin
from salute.workspace.models import WorkspaceAccount, WorkspaceAccountAlias


class WorkspaceAccountAliasInlineAdmin(admin.StackedInline):
    model = WorkspaceAccountAlias
    readonly_fields = ("address",)


@admin.register(WorkspaceAccount)
class WorkspaceAccountAdmin(BaseModelAdminMixin, admin.ModelAdmin):
    list_display = ("primary_email", "person", "org_unit_path")
    search_fields = ("primary_email", "given_name", "family_name")
    list_filter = (
        ("person", admin.EmptyFieldListFilter),
        "archived",
        "suspended",
        "is_admin",
        "is_delegated_admin",
        "is_enforced_in_2sv",
        "is_enrolled_in_2sv",
        "has_recovery_email",
        "has_recovery_phone",
    )
    readonly_fields = (
        "person",
        "google_id",
        "primary_email",
        "given_name",
        "family_name",
        "archived",
        "change_password_at_next_login",
        "suspended",
        "agreed_to_terms",
        "external_ids",
        "is_admin",
        "is_delegated_admin",
        "is_enforced_in_2sv",
        "is_enrolled_in_2sv",
        "org_unit_path",
        "has_recovery_email",
        "has_recovery_phone",
        "creation_time",
        "last_login_time",
    )
    inlines = (WorkspaceAccountAliasInlineAdmin,)

    fieldsets = (
        (None, {"fields": ("primary_email", "given_name", "family_name", "person", "google_id", "org_unit_path")}),
        (
            "Security",
            {
                "classes": ["collapse"],
                "fields": (
                    "archived",
                    "change_password_at_next_login",
                    "suspended",
                    "agreed_to_terms",
                    "external_ids",
                    "is_admin",
                    "is_delegated_admin",
                    "is_enforced_in_2sv",
                    "is_enrolled_in_2sv",
                    "has_recovery_email",
                    "has_recovery_phone",
                ),
            },
        ),
    ) + BaseModelAdminMixin.FIELDSETS
