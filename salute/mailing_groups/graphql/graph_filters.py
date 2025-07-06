# mypy: disable-error-code="misc"
from __future__ import annotations

import strawberry as sb
import strawberry_django as sd

from salute.mailing_groups import models
from salute.roles.graphql.graph_filters import TeamFilter


@sd.filter_type(models.SystemMailingGroup)
class SystemMailingGroupFilter:
    id: sd.BaseFilterLookup[sb.relay.GlobalID] | None = sb.UNSET
    teams: TeamFilter | None = sd.filter_field(
        description="Filter by team",
    )
