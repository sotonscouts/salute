from django.db import models

from salute.core.models import BaseModel
from salute.mailing_groups.models import SystemMailingGroup


class WorkspaceAccount(BaseModel):
    person = models.OneToOneField(
        "people.Person", null=True, on_delete=models.SET_NULL, related_name="workspace_account"
    )

    google_id = models.CharField(max_length=100, unique=True, editable=False)
    primary_email = models.CharField(max_length=255, unique=True, editable=False)
    given_name = models.CharField(max_length=255, editable=False)
    family_name = models.CharField(max_length=255, editable=False)

    # Editable Flags
    archived = models.BooleanField(editable=False)
    change_password_at_next_login = models.BooleanField(editable=False)
    suspended = models.BooleanField(editable=False)

    # Read Only Attributes
    agreed_to_terms = models.BooleanField(editable=False)
    external_ids = models.JSONField(editable=False)
    is_admin = models.BooleanField(editable=False)
    is_delegated_admin = models.BooleanField(editable=False)
    is_enforced_in_2sv = models.BooleanField(editable=False)
    is_enrolled_in_2sv = models.BooleanField(editable=False)
    org_unit_path = models.CharField(max_length=255, editable=False)

    # Security
    has_recovery_email = models.BooleanField(editable=False)
    has_recovery_phone = models.BooleanField(editable=False)

    # Timestamps
    creation_time = models.DateTimeField(editable=False)
    last_login_time = models.DateTimeField(null=True, editable=False)

    def __str__(self) -> str:
        return self.primary_email


class WorkspaceAccountAlias(BaseModel):
    account = models.ForeignKey(WorkspaceAccount, on_delete=models.CASCADE, related_name="aliases")
    address = models.EmailField(unique=True, editable=False)

    class Meta:
        verbose_name = "Workspace Account Alias"
        verbose_name_plural = "Workspace Account Aliases"

    def __str__(self) -> str:
        return self.address


class WorkspaceGroup(BaseModel):
    google_id = models.CharField(max_length=100, unique=True, editable=False)
    email = models.CharField(max_length=255, unique=True, editable=False)
    name = models.CharField(max_length=255, editable=False)
    description = models.TextField(editable=False)
    system_mailing_group = models.OneToOneField(
        SystemMailingGroup,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="workspace_group",
    )

    def __str__(self) -> str:
        return self.email


class WorkspaceGroupAlias(BaseModel):
    group = models.ForeignKey(WorkspaceGroup, on_delete=models.CASCADE, related_name="aliases")
    address = models.EmailField(unique=True, editable=False)

    class Meta:
        verbose_name = "Workspace Group Alias"
        verbose_name_plural = "Workspace Group Aliases"

    def __str__(self) -> str:
        return self.address
