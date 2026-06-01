from __future__ import annotations

import strawberry as sb
import strawberry_django as sd
from django.db.models import Q
from strawberry import UNSET
from strawberry_django.filters import apply as apply_filters

from salute.hierarchy import models as hierarchy_models
from salute.hierarchy.graphql.graph_filters import GroupFilter, SectionFilter
from salute.people.graphql.person_filters import group_filter_defines_criteria
from salute.people.models import role_team_in_groups_q
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

    @sd.filter_field(description="Filter by search query")
    def search(self, value: str, prefix: str) -> Q:
        return (
            Q(**{f"{prefix}team_type__display_name__icontains": value})
            | Q(**{f"{prefix}group__unit_name__icontains": value})
            | Q(**{f"{prefix}group__location_name__icontains": value})
        )


@sd.filter_type(models.Role)
class RoleFilter:
    id: sd.BaseFilterLookup[sb.relay.GlobalID] | None = sb.UNSET
    person: PersonFilter | None = sb.UNSET
    team: TeamFilter | None = sb.UNSET

    @sd.filter_field(
        filter_none=True,
        description=(
            "Role's team is scoped to a group matching this filter "
            "(group team, section team in that group, or sub-team of a group team)."
        ),
    )
    def group(self, value: GroupFilter | None, prefix: str) -> Q:
        if value is None or value is UNSET:
            return Q()
        if not group_filter_defines_criteria(value):
            return Q(pk__in=[])
        group_qs = apply_filters(value, hierarchy_models.Group.objects.all(), None)
        if not group_qs.exists():
            return Q(pk__in=[])
        return role_team_in_groups_q(group_qs, team_lookup_prefix=prefix)

    @sd.filter_field(description="Filter by whether the role is automatically assigned based on another role")
    def is_automatic(self, value: bool, prefix: str) -> Q:  # noqa: FBT001
        expr = Q(**{f"{prefix}status__name": "-"})
        if value:
            return expr
        return ~expr


@sd.filter_type(models.Accreditation)
class AccreditationFilter:
    id: sd.BaseFilterLookup[sb.relay.GlobalID] | None = sb.UNSET
    person: PersonFilter | None = sb.UNSET
    team: TeamFilter | None = sb.UNSET


@sd.filter_type(models.AccreditationType)
class AccreditationTypeFilter:
    id: sd.BaseFilterLookup[sb.relay.GlobalID] | None = sb.UNSET


@sd.filter_type(models.RoleType)
class RoleTypeFilter:
    id: sd.BaseFilterLookup[sb.relay.GlobalID] | None = sb.UNSET


# PersonFilter is imported here so ``RoleFilter`` / ``AccreditationFilter`` annotations resolve
# without a circular import (``person_filters`` must not import this module at load time).
from salute.people.graphql import person_filters as _person_filters  # noqa: E402
from salute.people.graphql.person_filters import PersonFilter  # noqa: E402

_person_filters.RoleFilter = RoleFilter  # type: ignore
