import strawberry as sb
import strawberry_django as sd
from strawberry_django.permissions import HasPerm

from salute.roles import models as roles_models
from salute.roles.graphql.graph_types import TeamType


@sb.type
class RolesQuery:
    @sd.field(
        description="Get a team type by ID",
        extensions=[HasPerm("team_type.view", message="You don't have permission to view that team type.")],
    )
    def team_type(self, team_type_id: sb.relay.GlobalID, info: sb.Info) -> TeamType:
        return roles_models.TeamType.objects.get(id=team_type_id.node_id)  # type: ignore[return-value]

    team_types: sd.relay.ListConnectionWithTotalCount[TeamType] = sd.connection(
        description="List groups",
        extensions=[
            HasPerm("team_type.list", message="You don't have permission to list team types.", fail_silently=False)
        ],
    )
