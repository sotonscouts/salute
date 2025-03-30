from django.conf import settings
from django.contrib import admin
from django.db import models
from django.http import HttpRequest

from salute.mailing_groups.models import SystemMailingGroup, SystemMailingGroupMembership


class SystemMailingGroupMembershipInline(admin.TabularInline):
    model = SystemMailingGroupMembership
    extra = 0
    verbose_name = "Member"
    hide_title = True

    readonly_fields = ("workspace_account",)

    @admin.display(description="Workspace Account", ordering="person__workspace_account")
    def workspace_account(self, obj: SystemMailingGroupMembership) -> str:
        return str(obj.person.workspace_account)

    def has_change_permission(self, request: HttpRequest, obj: models.Model | None = None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj: models.Model | None = None) -> bool:
        return False

    def has_add_permission(self, request: HttpRequest, obj: models.Model | None = None) -> bool:
        return False


class MailGroupAdmin(admin.ModelAdmin):
    list_display = ["name", "display_name", "member_count", "workspace_member_count"]
    readonly_fields = (
        "name",
        "display_name",
        "member_count",
        "workspace_member_count",
        "workspace_group",
        "can_members_send_as",
        "can_receive_external_email",
        "composite_key",
        "config",
    )
    search_fields = ["name", "display_name", "composite_key"]
    list_filter = ["can_receive_external_email", "can_members_send_as", ("workspace_group", admin.EmptyFieldListFilter)]
    inlines = [SystemMailingGroupMembershipInline]
    fieldsets = (
        (None, {"fields": ("name", "display_name")}),
        ("Stats", {"fields": ("member_count", "workspace_member_count")}),
        ("Google Workspace", {"fields": ("can_members_send_as", "can_receive_external_email", "workspace_group")}),
        ("Tech Details", {"classes": ("collapse",), "fields": ("composite_key", "config")}),
    )

    @admin.display(description="Member count", ordering="member_count")
    def member_count(self, obj: models.Model) -> int:
        return obj.member_count  # type: ignore[attr-defined]

    @admin.display(description="Account count", ordering="workspace_member_count")
    def workspace_member_count(self, obj: models.Model) -> int:
        return obj.workspace_member_count  # type: ignore[attr-defined]

    def get_queryset(self, request: HttpRequest) -> models.QuerySet[SystemMailingGroup]:
        return (
            super()
            .get_queryset(request)
            .annotate(
                member_count=models.Count("members"),
                workspace_member_count=models.Count(
                    "members", filter=models.Q(members__workspace_account__isnull=False)
                ),
            )
        )

    def has_change_permission(self, request: HttpRequest, obj: models.Model | None = None) -> bool:
        return request.user.is_superuser

    def has_delete_permission(self, request: HttpRequest, obj: models.Model | None = None) -> bool:
        return request.user.is_superuser and settings.DEBUG

    def has_add_permission(self, request: HttpRequest, obj: models.Model | None = None) -> bool:
        return False


admin.site.register(SystemMailingGroup, MailGroupAdmin)
