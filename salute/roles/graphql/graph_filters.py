import strawberry as sb
import strawberry_django as sd
from django.db.models import Q

from salute.people.graphql.graph_types import PersonFilter
from salute.roles import models


@sd.filter_type(models.TeamType)
class TeamTypeFilter:
    id: sd.BaseFilterLookup[sb.relay.GlobalID] | None = sb.UNSET


# TODO filters:
# - has_sub_teams
# - is_sub_team
# - parent_team
# - level (district, group, section) - note: includes sub teams


@sd.filter_type(models.Team)
class TeamFilter:
    id: sd.BaseFilterLookup[sb.relay.GlobalID] | None = sb.UNSET
    team_type: TeamTypeFilter | None = sd.filter_field(
        description="Filter by team type",
    )


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
