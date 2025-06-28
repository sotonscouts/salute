# mypy: disable-error-code="misc"
from __future__ import annotations

from datetime import datetime
from string import Template
from typing import Any, cast

import strawberry as sb
import strawberry_django as sd
from django.conf import settings
from django.db.models import Q, QuerySet
from strawberry_django.auth.utils import get_current_user
from strawberry_django.permissions import HasPerm

from salute.accounts.models import User
from salute.hierarchy.graphql.graph_types import District, Group, Section
from salute.mailing_groups import models as mailing_groups_models
from salute.mailing_groups.graphql.graph_types import SystemMailingGroup
from salute.people.graphql.graph_types import Person, PersonFilter
from salute.roles import models


@sd.type(models.AccreditationType)
class AccreditationType(sb.relay.Node):
    name: sb.Private[str]

    @sd.field(description="Formatted name for the accreditation type", only="name")
    def display_name(self, info: sb.Info) -> str:
        return self.name


@sd.type(models.RoleStatus)
class RoleStatus(sb.relay.Node):
    name: sb.Private[str]

    @sd.field(description="Formatted name for the role status", only="name")
    def display_name(self, info: sb.Info) -> str:
        return self.name


@sd.type(models.RoleType)
class RoleType(sb.relay.Node):
    name: sb.Private[str]

    @sd.field(description="Formatted name for the role type", only="name")
    def display_name(self, info: sb.Info) -> str:
        return self.name


@sd.type(models.TeamType)
class TeamType(sb.relay.Node):
    display_name: str = sd.field(description="Formatted name for the team type", only="name")


# TODO filters:
# - has_sub_teams
# - is_sub_team
# - parent_team
# - level (district, group, section) - note: includes sub teams


@sd.filter_type(models.Team, lookups=True)
class TeamFilter:
    id: sd.BaseFilterLookup[sb.relay.GlobalID] | None = sb.UNSET


@sd.interface(models.Team)
class TeamInterface(sb.relay.Node):
    team_type: TeamType = sb.field(description="The type of the team")
    display_name: str = sd.field(
        description="The formatted name of the team",
        select_related=["team_type", "parent_team", "district", "group", "section"],
    )

    roles: sd.relay.DjangoListConnection[Role] = sd.connection(
        description="List roles",
        extensions=[HasPerm("role.list", message="You don't have permission to list roles.", fail_silently=False)],
    )

    accreditations: sd.relay.DjangoListConnection[Accreditation] = sd.connection(
        description="List accreditations",
        extensions=[
            HasPerm(
                "accreditation.list", message="You don't have permission to list accreditations.", fail_silently=False
            )
        ],
    )

    @sd.field(
        description="The system mailing groups that this team belongs to. Only returns fully configured mailing groups.",  # noqa: E501
    )
    def system_mailing_groups(self) -> list[SystemMailingGroup]:
        return mailing_groups_models.SystemMailingGroup.objects.filter(
            teams=self, workspace_group__isnull=False
        ).order_by("name")  # type: ignore[return-value]

    @sd.field(
        description="Link to the TSA unit details.",
    )
    def tsa_details_link(self) -> str:
        template = Template(settings.TSA_TEAM_LINK_TEMPLATE)
        return template.safe_substitute(unitid=self.unit.tsa_id, teamtypeid=self.team_type.tsa_id)  # type: ignore[attr-defined]


@sd.type(models.Team, filters=TeamFilter)
class SubTeam(TeamInterface, sb.relay.Node):
    parent_team: Team = sb.field(description="The parent team of this team")


@sd.interface(models.Team)
class TeamWithChildInterface(TeamInterface, sb.relay.Node):
    @sd.field(description="The sub-teams of the team")
    def sub_teams(self, info: sb.Info) -> list[SubTeam]:
        return self.sub_teams.all()


@sd.type(models.Team, filters=TeamFilter)
class DistrictTeam(TeamWithChildInterface, sb.relay.Node):
    district: District = sb.field(description="The district that this team belongs to")


@sd.type(models.Team, filters=TeamFilter)
class GroupTeam(TeamWithChildInterface, sb.relay.Node):
    group: Group = sb.field(description="The section that this team belongs to")


@sd.type(models.Team, filters=TeamFilter)
class SectionTeam(TeamInterface, sb.relay.Node):
    section: Section = sb.field(description="The section that this team belongs to")


@sb.type
class UnitInfo:
    display_name: str = sb.field(description="Formatted name for the unit")


@sd.type(models.Team, filters=TeamFilter)
class Team(TeamWithChildInterface, sb.relay.Node):
    parent_team: Team | None = sb.field(description="The parent team of this team")
    district: District | None = sb.field(description="The district that this team belongs to")
    group: Group | None = sb.field(description="The section that this team belongs to")
    section: Section | None = sb.field(description="The section that this team belongs to")

    @sd.field()  # TODO: optimise
    def unit(self, info: sb.Info) -> UnitInfo:
        return UnitInfo(display_name=self.unit.display_name)


@sd.filter_type(models.Role)
class RoleFilter:
    person: PersonFilter | None
    team: TeamFilter | None

    @sd.filter_field(description="Filter by whether the role is automatically assigned based on another role")
    def is_automatic(self, value: bool, prefix: str) -> Q:  # noqa: FBT001
        expr = Q(**{f"{prefix}status__name": "-"})
        if value:
            return expr
        return ~expr


@sd.type(models.Role, filters=RoleFilter)
class Role(sb.relay.Node):
    person: Person = sb.field(description="The person the role belongs to")
    team: Team = sb.field(description="The team the role belongs to")
    role_type: RoleType = sb.field(description="The type of role within the team")
    status: RoleStatus = sb.field(description="The status of the role")

    @classmethod
    def get_queryset(
        cls, queryset: models.RoleQuerySet | QuerySet, info: sb.Info, **kwargs: Any
    ) -> models.RoleQuerySet | QuerySet:
        user = get_current_user(info)
        if not user.is_authenticated:
            return queryset.none()

        user = cast(User, user)
        # When the strawberry optimiser is determining the queryset relations, it will call this method.
        # In such calls, the queryset is not a PersonQuerySet, but a Django QuerySet.
        if hasattr(queryset, "for_user"):
            return queryset.for_user(user)
        return queryset


@sd.filter_type(models.Accreditation)
class AccreditationFilter:
    person: PersonFilter | None
    team: TeamFilter | None


@sd.type(models.Accreditation, filters=AccreditationFilter)
class Accreditation(sb.relay.Node):
    person: Person = sb.field(description="The person the accreditation is assigned to")
    team: Team = sb.field(description="The team the accreditation is assigned to")
    accreditation_type: AccreditationType = sb.field(description="The type of accreditation")
    status: str = sb.field(description="The status of the accreditation")
    expires_at: datetime = sb.field(description="The date when the accreditation expires")
    granted_at: datetime = sb.field(description="The date when the accreditation was granted")

    @classmethod
    def get_queryset(
        cls, queryset: models.AccreditationQuerySet | QuerySet, info: sb.Info, **kwargs: Any
    ) -> models.AccreditationQuerySet | QuerySet:
        user = get_current_user(info)
        if not user.is_authenticated:
            return queryset.none()

        user = cast(User, user)
        # When the strawberry optimiser is determining the queryset relations, it will call this method.
        # In such calls, the queryset is not a AccreditationQuerySet, but a Django QuerySet.
        if hasattr(queryset, "for_user"):
            return queryset.for_user(user)
        return queryset
