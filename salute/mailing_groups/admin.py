import uuid

from django.conf import settings
from django.contrib import admin, messages
from django.db import models
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import URLPattern, path, reverse

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

    def get_urls(self) -> list[URLPattern]:
        urls = super().get_urls()
        custom_urls = [
            path(
                "<uuid:mailing_group_id>/create-workspace-group/",
                self.admin_site.admin_view(self.create_workspace_group_view),
                name="create-workspace-group",
            ),
        ]
        return custom_urls + urls

    def create_workspace_group_view(
        self, request: HttpRequest, mailing_group_id: uuid.UUID
    ) -> HttpResponseRedirect | HttpResponse:
        # Check permission
        if not request.user.is_superuser:
            messages.error(request, "You don't have permission to create workspace groups")
            return HttpResponseRedirect(
                reverse("admin:mailing_groups_systemmailinggroup_change", args=[mailing_group_id])
            )

        mailing_group = SystemMailingGroup.objects.get(pk=mailing_group_id)

        # Check if workspace group already exists
        try:
            if mailing_group.workspace_group:
                messages.error(request, f"Workspace group already exists for {mailing_group.name}")
                return HttpResponseRedirect(
                    reverse("admin:mailing_groups_systemmailinggroup_change", args=[mailing_group_id])
                )
        except SystemMailingGroup.workspace_group.RelatedObjectDoesNotExist:
            # Workspace group doesn't exist, continue with creation
            pass

        # Handle confirmation page
        if request.method == "GET":
            context = {
                "title": f"Create workspace group for {mailing_group.name}",
                "mailing_group": mailing_group,
                "opts": self.model._meta,
                "app_label": self.model._meta.app_label,
            }
            return render(request, "admin/mailing_groups/create_workspace_group_confirmation.html", context)

        # Handle POST request (confirmation)
        elif request.method == "POST":
            # Import Google API libraries
            from google.oauth2 import service_account
            from googleapiclient.discovery import build

            from salute.integrations.workspace.management.commands.sync_workspace_groups import (
                SALUTE_MANAGED_GROUP_EMAIL_SUFFIX,
                SCOPES,
            )

            # Import here to avoid circular imports
            from salute.integrations.workspace.models import WorkspaceGroup

            try:
                # Set up credentials for Google Workspace API
                credentials = service_account.Credentials.from_service_account_file("credentials.json", scopes=SCOPES)  # type: ignore[no-untyped-call]
                delegated_credentials = credentials.with_subject("dan.trickey@southamptoncityscouts.org.uk")

                # Create services
                directory_service = build("admin", "directory_v1", credentials=delegated_credentials)

                # Prepare group details
                expected_email = mailing_group.name + SALUTE_MANAGED_GROUP_EMAIL_SUFFIX
                expected_name = mailing_group.display_name

                # Create the group in Google Workspace
                try:
                    group_data = {
                        "email": expected_email,
                        "name": expected_name,
                        "description": "New group created by Salute - Awaiting setup",
                    }
                    created_group = directory_service.groups().insert(body=group_data).execute()
                    google_id = created_group.get("id")

                    # 3. Create local WorkspaceGroup
                    workspace_group = WorkspaceGroup.objects.create(
                        google_id=google_id,
                        email=expected_email,
                        name=expected_name,
                        description="",
                        system_mailing_group=mailing_group,
                    )

                    messages.success(
                        request,
                        f"Google Workspace group '{workspace_group}' successfully created and connected to {mailing_group.name}.",  # noqa: E501
                    )
                except Exception as api_error:  # noqa: BLE001
                    messages.error(request, f"Error creating Google Workspace group: {str(api_error)}")
                    return HttpResponseRedirect(
                        reverse("admin:mailing_groups_systemmailinggroup_change", args=[mailing_group_id])
                    )

            except Exception as e:  # noqa: BLE001
                messages.error(request, f"Error setting up Google Workspace API: {str(e)}")

        return HttpResponseRedirect(reverse("admin:mailing_groups_systemmailinggroup_change", args=[mailing_group_id]))

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

    def response_change(self, request: HttpRequest, obj: SystemMailingGroup) -> HttpResponseRedirect:
        """
        Override the response_change method to add a custom button to the admin form
        """
        # Check if workspace group already exists
        try:
            if obj.workspace_group:
                pass  # Group exists, don't add a button
            else:
                # This shouldn't happen as the check above would raise an exception
                pass
        except SystemMailingGroup.workspace_group.RelatedObjectDoesNotExist:
            # Add a button to create a workspace group
            if "_create_workspace_group" in request.POST:
                url = reverse("admin:create-workspace-group", args=[obj.pk])
                return HttpResponseRedirect(url)

        return super().response_change(request, obj)  # type: ignore[return-value]

    def render_change_form(
        self,
        request: HttpRequest,
        context: dict,
        add: bool = False,  # noqa: FBT001,FBT002
        change: bool = False,  # noqa: FBT001,FBT002
        form_url: str = "",
        obj: SystemMailingGroup | None = None,
    ) -> HttpResponse:
        """
        Override the render_change_form method to add a custom button to the admin form
        """
        if obj and request.user.is_superuser:
            try:
                if not obj.workspace_group:
                    pass
            except SystemMailingGroup.workspace_group.RelatedObjectDoesNotExist:
                # Add a button to create a workspace group
                context.setdefault("submit_row", {})
                context["submit_row"] = {
                    **context.get("submit_row", {}),
                    "show_create_workspace_group": True,
                }

        return super().render_change_form(request, context, add, change, form_url, obj)


admin.site.register(SystemMailingGroup, MailGroupAdmin)
