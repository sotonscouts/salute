# mypy: disable-error-code="misc"
from __future__ import annotations

import strawberry as sb
import strawberry_django as sd

from salute.hierarchy.graphql.graph_types import District, Group, Section
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
    name: sb.Private[str]

    @sd.field(description="Formatted name for the team type", only="name")
    def display_name(self, info: sb.Info) -> str:
        return self.name


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


@sd.type(models.Team)
class Team(TeamWithChildInterface, sb.relay.Node):
    parent_team: Team | None = sb.field(description="The parent team of this team")
    district: District | None = sb.field(description="The district that this team belongs to")
    group: Group | None = sb.field(description="The section that this team belongs to")
    section: Section | None = sb.field(description="The section that this team belongs to")
