from __future__ import annotations

from django.db import models

from salute.core.models import BaseModel, Taxonomy
from salute.hierarchy.models import District, Group, Section
from salute.integrations.tsa.models import TSAObject, TSATaxonomy


class TeamType(TSATaxonomy):
    nickname = models.CharField(
        max_length=255,
        blank=True,
        help_text='Used to override name from TSA. Include "Team", e.g "People Team"',
    )
    display_name = models.GeneratedField(
        expression=models.Case(
            models.When(~models.Q(nickname__exact=""), models.F("nickname")),
            default=models.F("name"),
        ),
        output_field=models.CharField(max_length=255),
        db_persist=True,
    )

    # Mailing Lists
    mailing_slug = models.CharField(
        max_length=64,
        blank=True,
        help_text="Slug for generating mailing lists. Do not change unless you understand the impact.",
    )
    has_team_lead = models.BooleanField(default=False)
    has_all_list = models.BooleanField(default=False, help_text="If has sub-teams, whether to generate a -all list.")
    included_in_all_members = models.BooleanField(default=True, help_text="Included in all members -all addresses")

    def __str__(self) -> str:
        return self.display_name

    class Meta:
        ordering = ("display_name",)


class Team(BaseModel):
    team_type = models.ForeignKey(TeamType, on_delete=models.PROTECT)

    district = models.ForeignKey(District, null=True, on_delete=models.PROTECT, related_name="teams")
    group = models.ForeignKey(Group, null=True, on_delete=models.PROTECT, related_name="teams")
    section = models.ForeignKey(Section, null=True, on_delete=models.PROTECT, related_name="teams")
    parent_team = models.ForeignKey("Team", null=True, on_delete=models.PROTECT, related_name="sub_teams")

    allow_sub_team = models.BooleanField()
    inherit_permissions = models.BooleanField()

    TSA_FIELDS: tuple[str, ...] = (
        "team_type",
        "district",
        "group",
        "section",
        "parent_team",
        "allow_sub_team",
        "inherit_permissions",
    )

    class Meta:
        ordering = ("team_type__display_name",)
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(  # District
                        district__isnull=False, group__isnull=True, section__isnull=True, parent_team__isnull=True
                    )
                    | models.Q(  # Group
                        district__isnull=True, group__isnull=False, section__isnull=True, parent_team__isnull=True
                    )
                    | models.Q(  # Section
                        district__isnull=True, group__isnull=True, section__isnull=False, parent_team__isnull=True
                    )
                    | models.Q(  # Parent Team
                        district__isnull=True, group__isnull=True, section__isnull=True, parent_team__isnull=False
                    )
                ),
                name="team_only_has_one_parent_object",
                violation_error_message="A team must have exactly one parent",
            ),
            models.UniqueConstraint(
                fields=["team_type", "district"],
                condition=models.Q(district__isnull=False),
                name="unique_team_within_district",
            ),
            models.UniqueConstraint(
                fields=["team_type", "group"], condition=models.Q(group__isnull=False), name="unique_team_within_group"
            ),
            models.UniqueConstraint(
                fields=["team_type", "section"],
                condition=models.Q(section__isnull=False),
                name="unique_team_within_section",
            ),
            models.UniqueConstraint(
                fields=["team_type", "parent_team"],
                condition=models.Q(parent_team__isnull=False),
                name="unique_team_within_parent_team",
            ),
        ]

    def __str__(self) -> str:
        return self.display_name

    @property
    def display_name(self) -> str:
        return f"{self.team_type.display_name} - {self.unit}"

    @property
    def parent(self) -> District | Group | Section | Team:
        parent = self.district or self.group or self.section or self.parent_team
        assert parent is not None  # Enforced by check constraint
        return parent

    @property
    def unit(self) -> District | Group | Section:
        if isinstance(self.parent, Team):
            return self.parent.unit

        unit = self.district or self.group or self.section
        assert unit is not None  # Enforced by check constraint
        return unit


class RoleType(Taxonomy):
    TSA_FIELDS = ("name",)


class RoleStatus(Taxonomy):
    TSA_FIELDS = ("name",)

    class Meta(Taxonomy.Meta):
        verbose_name_plural = "role statuses"


class Role(TSAObject):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="roles")
    person = models.ForeignKey("people.Person", on_delete=models.CASCADE, related_name="roles")

    role_type = models.ForeignKey(RoleType, on_delete=models.PROTECT, related_name="roles")
    status = models.ForeignKey(RoleStatus, on_delete=models.PROTECT, related_name="roles")

    TSA_FIELDS = ("team", "person", "role_type", "status")

    class Meta:
        ordering = ("team", "role_type", "person")

    def __str__(self) -> str:
        return f"{self.person} is {self.role_type.name} for {self.team}"


class AccreditationType(TSATaxonomy):
    pass


class Accreditation(TSAObject):
    accreditation_type = models.ForeignKey(AccreditationType, on_delete=models.PROTECT, related_name="accreditations")
    person = models.ForeignKey("people.Person", on_delete=models.CASCADE, related_name="accreditations")
    team = models.ForeignKey(Team, on_delete=models.PROTECT, related_name="accreditations")
    status = models.CharField(max_length=64)
    expires_at = models.DateTimeField()
    granted_at = models.DateTimeField()

    TSA_FIELDS = ("team", "person", "accreditation_type", "status", "expires_at", "granted_at")

    def __str__(self) -> str:
        return f"{self.accreditation_type} for {self.person} in {self.team}"
