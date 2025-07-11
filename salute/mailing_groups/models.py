from __future__ import annotations

from typing import TYPE_CHECKING, Never

from django.db import models

from salute.core.models import BaseModel
from salute.hierarchy.constants import GROUP_SECTION_TYPE_OPTIONS
from salute.mailing_groups.schema import MailGroupConfig

if TYPE_CHECKING:
    from django.db.models.fields.related import ManyToManyField

    from salute.people.models import Person
    from salute.roles.models import Team


class GroupSectionMailingPreferenceOption(models.TextChoices):
    TEAMS = "TEAMS", "Teams (Recommended, Default)"
    LEADERS = "LEADERS", "Team Leaders"


class GroupSectionSystemMailingPreference(BaseModel):
    group = models.ForeignKey("hierarchy.Group", on_delete=models.CASCADE)
    section_type = models.CharField(max_length=32, choices=GROUP_SECTION_TYPE_OPTIONS)
    mailing_preference = models.CharField(
        max_length=32,
        choices=GroupSectionMailingPreferenceOption.choices,
        default=GroupSectionMailingPreferenceOption.TEAMS,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["group", "section_type"],
                name="unique_group_section_type",
                violation_error_message="Mailing preference already exists for this group and section type.",
            )
        ]

    def __str__(self) -> str:
        return f"{self.group} - {self.section_type} - {self.mailing_preference}"


class SystemMailingGroup(BaseModel):
    name = models.CharField(max_length=255, unique=True)
    display_name = models.CharField(max_length=255)
    short_name = models.CharField(max_length=255)
    composite_key = models.CharField(max_length=255, unique=True)
    config = models.JSONField()
    can_receive_external_email = models.BooleanField(
        default=True, help_text="Whether the group can receive emails externally."
    )
    can_members_send_as = models.BooleanField(
        default=False, help_text="Whether members can send emails as the group address."
    )

    fallback_group_composite_key = models.CharField(
        max_length=255,
        blank=True,
        help_text="The composite key of the fallback group to use if there are no members in this group.",
    )
    always_include_fallback_group = models.BooleanField(
        default=False,
        help_text="Whether to always include the fallback group in this group.",
    )

    teams: ManyToManyField[Team, Never] = models.ManyToManyField(  # type: ignore[assignment]
        "roles.Team",
        blank=True,
        editable=False,
        related_name="system_mailing_groups",
        help_text="The teams that this mailing group belongs to.",
    )
    members: ManyToManyField[Person, Never] = models.ManyToManyField(
        "people.Person", related_name="system_mailing_groups", through="SystemMailingGroupMembership"
    )

    def update_members(self) -> None:
        config = MailGroupConfig.model_validate(self.config)
        members = config.get_members()
        self.members.set(members)

    def __str__(self) -> str:
        return self.name

    class Meta:
        ordering = ["name"]

    @property
    def fallback_group(self) -> SystemMailingGroup | None:
        if self.fallback_group_composite_key:
            return SystemMailingGroup.objects.filter(composite_key=self.fallback_group_composite_key).first()
        return None


class SystemMailingGroupMembership(BaseModel):
    person = models.ForeignKey("people.Person", on_delete=models.CASCADE)
    system_mailing_group = models.ForeignKey(SystemMailingGroup, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["person", "system_mailing_group"], name="unique_person_system_mailing_group"
            )
        ]

    def __str__(self) -> str:
        return f"{self.person} is member of {self.system_mailing_group}"
