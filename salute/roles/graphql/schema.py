import strawberry as sb
import strawberry_django as sd
from strawberry_django.permissions import HasPerm

from salute.roles import models as roles_models
from salute.roles.graphql.graph_types import RoleType, TeamType


@sb.type
class RolesQuery:
    @sd.field(
        description="Get a team type by ID",
        extensions=[HasPerm("team_type.view", message="You don't have permission to view that team type.")],
    )
    def team_type(self, team_type_id: sb.relay.GlobalID, info: sb.Info) -> TeamType:
        return roles_models.TeamType.objects.get(id=team_type_id.node_id)  # type: ignore[return-value]

    team_types: sd.relay.ListConnectionWithTotalCount[TeamType] = sd.connection(
        description="List team types",
        extensions=[
            HasPerm("team_type.list", message="You don't have permission to list team types.", fail_silently=False)
        ],
    )

    @sd.field(
        description="Get a role type by ID",
        extensions=[HasPerm("role_type.view", message="You don't have permission to view that role type.")],
    )
    def role_type(self, role_type_id: sb.relay.GlobalID, info: sb.Info) -> RoleType:
        return roles_models.RoleType.objects.get(id=role_type_id.node_id)  # type: ignore[return-value]

    role_types: sd.relay.ListConnectionWithTotalCount[RoleType] = sd.connection(
        description="List role types",
        extensions=[
            HasPerm("role_type.list", message="You don't have permission to list role types.", fail_silently=False)
        ],
    )
