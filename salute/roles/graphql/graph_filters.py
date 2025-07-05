from __future__ import annotations

import strawberry as sb
import strawberry_django as sd
from django.db.models import Q

from salute.hierarchy.graphql.graph_filters import GroupFilter, SectionFilter
from salute.people.graphql.graph_types import PersonFilter
from salute.roles import models


@sd.filter_type(models.TeamType)
class TeamTypeFilter:
    id: sd.BaseFilterLookup[sb.relay.GlobalID] | None = sb.UNSET


@sd.filter_type(models.Team)
class TeamFilter:
    id: sd.BaseFilterLookup[sb.relay.GlobalID] | None = sb.UNSET
    team_type: TeamTypeFilter | None = sd.filter_field(
        description="Filter by team type",
    )
    level: sd.BaseFilterLookup[models.TeamLevel] | None = sd.filter_field(
        description="Filter by team level",
    )
    group: GroupFilter | None = sd.filter_field(
        description="Filter by group",
        filter_none=True,
    )
    section: SectionFilter | None = sd.filter_field(
        description="Filter by section",
        filter_none=True,
    )
    parent_team: TeamFilter | None = sd.filter_field(
        description="Filter by parent team",
        filter_none=True,
    )

    @sd.filter_field(description="Filter by whether the team is a sub-team")
    def is_sub_team(self, value: bool, prefix: str) -> Q:  # noqa: FBT001
        expr = Q(**{f"{prefix}parent_team__isnull": False})
        if value:
            return expr
        return ~expr


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


@sd.filter_type(models.Accreditation)
class AccreditationFilter:
    person: PersonFilter | None
    team: TeamFilter | None
