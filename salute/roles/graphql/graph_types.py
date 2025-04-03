# mypy: disable-error-code="misc"
from __future__ import annotations

from typing import Any, cast

import strawberry as sb
import strawberry_django as sd
from django.db.models import QuerySet
from strawberry_django.auth.utils import get_current_user
from strawberry_django.permissions import HasPerm

from salute.accounts.models import User
from salute.hierarchy.graphql.graph_types import District, Group, Section
from salute.people.graphql.graph_types import Person
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


@sd.interface(models.Team)
class TeamInterface(sb.relay.Node):
    team_type: TeamType = sb.field(description="The type of the team")
    display_name: str = sd.field(
        description="The formatted name of the team",
        select_related=["team_type", "parent_team", "district", "group", "section"],
    )

    roles: sd.relay.ListConnectionWithTotalCount[Role] = sd.connection(
        description="List roles",
        extensions=[HasPerm("role.list", message="You don't have permission to list roles.", fail_silently=False)],
    )


@sd.type(models.Team)
class SubTeam(TeamInterface, sb.relay.Node):
    parent_team: Team = sb.field(description="The parent team of this team")


@sd.interface(models.Team)
class TeamWithChildInterface(TeamInterface, sb.relay.Node):
    @sd.field(description="The sub-teams of the team")
    def sub_teams(self, info: sb.Info) -> list[SubTeam]:
        return self.sub_teams.all()


@sd.type(models.Team)
class DistrictTeam(TeamWithChildInterface, sb.relay.Node):
    district: District = sb.field(description="The district that this team belongs to")


@sd.type(models.Team)
class GroupTeam(TeamWithChildInterface, sb.relay.Node):
    group: Group = sb.field(description="The section that this team belongs to")


@sd.type(models.Team)
class SectionTeam(TeamInterface, sb.relay.Node):
    section: Section = sb.field(description="The section that this team belongs to")


@sb.type
class UnitInfo:
    display_name: str = sb.field(description="Formatted name for the unit")


@sd.type(models.Team)
class Team(TeamWithChildInterface, sb.relay.Node):
    parent_team: Team | None = sb.field(description="The parent team of this team")
    district: District | None = sb.field(description="The district that this team belongs to")
    group: Group | None = sb.field(description="The section that this team belongs to")
    section: Section | None = sb.field(description="The section that this team belongs to")

    @sd.field()  # TODO: optimise
    def unit(self, info: sb.Info) -> UnitInfo:
        return UnitInfo(display_name=self.unit.display_name)


@sd.type(models.Role)
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
