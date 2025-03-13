from django.contrib import admin
from django.http import HttpRequest

from salute.core.admin import BaseModelAdminMixin
from salute.core.models import BaseModel
from salute.integrations.tsa.admin import TSAObjectModelAdminMixin

from .models import Accreditation, AccreditationType, Role, RoleStatus, RoleType, Team, TeamType


class TeamRoleInlineAdmin(admin.TabularInline):
    model = Role
    readonly_fields = Role.TSA_FIELDS


class TeamAccreditationInlineAdmin(admin.TabularInline):
    model = Accreditation
    readonly_fields = Accreditation.TSA_FIELDS


class TeamInlineAdmin(admin.TabularInline):
    model = Team
    show_change_link = True
    fields = ("team_type", "role_count", "accreditation_count")
    readonly_fields = ("team_type", "role_count", "accreditation_count")

    @admin.display(description="Role count")
    def role_count(self, obj: Team) -> int:
        return obj.roles.count()

    @admin.display(description="Accreditation count")
    def accreditation_count(self, obj: Team) -> int:
        return obj.accreditations.count()


@admin.register(TeamType)
class TeamTypeAdmin(TSAObjectModelAdminMixin, admin.ModelAdmin):
    list_display = ("display_name", "mailing_slug")
    search_fields = ("name", "nickname", "tsa_id")

    fieldsets = (
        (None, {"fields": ("name", "display_name", "nickname")}),
        ("Mail Settings", {"fields": ("mailing_slug", "has_team_lead", "has_all_list", "included_in_all_members")}),
    ) + TSAObjectModelAdminMixin.FIELDSETS

    def get_readonly_fields(self, request: HttpRequest, obj: TeamType | None = None) -> list[str]:  # type: ignore[override]
        return super().get_readonly_fields(request, obj) + [
            "display_name",
            "mailing_slug",
            "has_team_lead",
            "has_all_list",
            "included_in_all_members",
        ]

    def has_change_permission(self, request: HttpRequest, obj: BaseModel | None = None) -> bool:
        return request.user.is_superuser


@admin.register(RoleType)
class RoleTypeAdmin(BaseModelAdminMixin, admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name", "tsa_id")

    fieldsets = ((None, {"fields": ("name",)}),) + BaseModelAdminMixin.FIELDSETS


@admin.register(RoleStatus)
class RoleStatusAdmin(BaseModelAdminMixin, admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)

    fieldsets = ((None, {"fields": ("name",)}),) + BaseModelAdminMixin.FIELDSETS


@admin.register(Team)
class TeamAdmin(BaseModelAdminMixin, admin.ModelAdmin):
    list_display = ("__str__", "team_type", "parent", "role_count")
    search_fields = ("team_type__name",)
    list_filter = ("allow_sub_team", "inherit_permissions", "team_type", "group")
    inlines = (TeamRoleInlineAdmin, TeamAccreditationInlineAdmin, TeamInlineAdmin)

    fieldsets = (
        (None, {"fields": ("team_type", "parent")}),
        ("Parent", {"fields": ("district", "group", "section", "parent_team")}),
        ("TSA Permissions", {"fields": ("allow_sub_team", "inherit_permissions")}),
        (
            "IDs",
            {"fields": ("id",)},
        ),
        (
            "Dates",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    def get_readonly_fields(self, request: HttpRequest, obj: Team | None = None) -> list[str]:  # type: ignore[override]
        return list(super().get_readonly_fields(request, obj)) + ["parent"]

    @admin.display(description="Role count")
    def role_count(self, obj: Team) -> int:
        return obj.roles.count()


@admin.register(Role)
class RoleAdmin(TSAObjectModelAdminMixin, admin.ModelAdmin):
    list_display = ("person", "team", "role_type", "status")
    list_filter = (
        "role_type",
        "team__team_type",
        ("person__workspace_account", admin.EmptyFieldListFilter),
        ("person__workspace_account__is_enrolled_in_2sv", admin.BooleanFieldListFilter),
    )
    search_fields = ("person__display_name", "team__team_type__name", "role_type__name")

    fieldsets = (
        (None, {"fields": ("person", "team")}),
        ("Details", {"fields": ("role_type", "status")}),
    ) + TSAObjectModelAdminMixin.FIELDSETS


@admin.register(AccreditationType)
class AccreditationTypeAdmin(TSAObjectModelAdminMixin, admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)
    inlines = (TeamAccreditationInlineAdmin,)

    fieldsets = ((None, {"fields": ("name",)}),) + TSAObjectModelAdminMixin.FIELDSETS


@admin.register(Accreditation)
class AccreditationAdmin(TSAObjectModelAdminMixin, admin.ModelAdmin):
    list_display = ("person", "team", "accreditation_type", "status")
    list_filter = ("accreditation_type",)
    search_fields = ("person__display_name", "team__team_type__name", "accreditation_type__name")

    fieldsets = (
        (None, {"fields": ("person", "team")}),
        ("Details", {"fields": ("accreditation_type", "status", "expires_at", "granted_at")}),
    ) + TSAObjectModelAdminMixin.FIELDSETS
