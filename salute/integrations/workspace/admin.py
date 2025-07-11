from django.contrib import admin
from django.db import models
from django.http import HttpRequest

from salute.core.admin import BaseModelAdminMixin
from salute.core.models import BaseModel
from salute.integrations.workspace.models import (
    WorkspaceAccount,
    WorkspaceAccountAlias,
    WorkspaceGroup,
    WorkspaceGroupAlias,
)


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


class WorkspaceGroupAliasInlineAdmin(admin.StackedInline):
    model = WorkspaceGroupAlias
    readonly_fields = ("address",)

    def has_change_permission(self, request: HttpRequest, obj: models.Model | None = None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj: models.Model | None = None) -> bool:
        return False

    def has_add_permission(self, request: HttpRequest, obj: models.Model | None = None) -> bool:
        return False


@admin.register(WorkspaceGroup)
class WorkspaceGroupAdmin(BaseModelAdminMixin, admin.ModelAdmin):
    list_display = ("email", "name", "system_mailing_group")
    list_filter = (("system_mailing_group", admin.EmptyFieldListFilter),)
    search_fields = ("email", "name", "description", "system_mailing_group__name")
    inlines = (WorkspaceGroupAliasInlineAdmin,)

    def get_readonly_fields(self, request: HttpRequest, obj: BaseModel | None = None) -> list[str]:
        return super().get_readonly_fields(request, obj) + [
            "google_id",
            "email",
            "name",
            "description",
        ]

    fieldsets = (
        (None, {"fields": ("email", "name", "description", "google_id", "system_mailing_group")}),
    ) + BaseModelAdminMixin.FIELDSETS

    def has_change_permission(self, request: HttpRequest, obj: BaseModel | None = None) -> bool:
        assert request.user.is_authenticated
        return request.user.is_superuser
