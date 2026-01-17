import strawberry as sb
import strawberry_django as sd
from strawberry_django.permissions import HasPerm, HasRetvalPerm

from salute.roles import models as roles_models
from salute.roles.graphql.graph_types import (
    Accreditation,
    AccreditationType,
    Role,
    RoleStatus,
    RoleType,
    Team,
    TeamType,
)


@sb.type
class RolesQuery:
    @sd.field(
        description="Get a accreditation type by ID",
        extensions=[
            HasPerm("accreditation_type.view", message="You don't have permission to view that accreditation type.")
        ],
        deprecation_reason="Use the `accreditation_types` field instead.",
    )
    def accreditation_type(self, accreditation_type_id: sb.relay.GlobalID, info: sb.Info) -> AccreditationType:
        return roles_models.AccreditationType.objects.get(id=accreditation_type_id.node_id)  # type: ignore[return-value]

    accreditation_types: sd.relay.DjangoListConnection[AccreditationType] = sd.connection(
        description="List accreditation types",
        extensions=[
            HasPerm(
                "accreditation_type.list",
                message="You don't have permission to list accreditation types.",
                fail_silently=False,
            )
        ],
    )

    @sd.field(
        description="Get all possible role statuses",
        extensions=[
            HasPerm("role_status.list", message="You don't have permission to list role statuses.", fail_silently=False)
        ],
    )
    def role_statuses(self, info: sb.Info) -> list[RoleStatus]:
        return roles_models.RoleStatus.objects.all()  # type: ignore[return-value]

    @sd.field(
        description="Get a role type by ID",
        extensions=[HasPerm("role_type.view", message="You don't have permission to view that role type.")],
        deprecation_reason="Use the `role_types` field instead.",
    )
    def role_type(self, role_type_id: sb.relay.GlobalID, info: sb.Info) -> RoleType:
        return roles_models.RoleType.objects.get(id=role_type_id.node_id)  # type: ignore[return-value]

    role_types: sd.relay.DjangoListConnection[RoleType] = sd.connection(
        description="List role types",
        extensions=[
            HasPerm("role_type.list", message="You don't have permission to list role types.", fail_silently=False)
        ],
    )

    teams: sd.relay.DjangoListConnection[Team] = sd.connection(
        description="List teams",
        # This endpoint, whilst not N+1, can make a lot of db queries as each team and unit are fetched.
        # So limit results to 20
        max_results=20,
        extensions=[HasPerm("team.list", message="You don't have permission to list teams.", fail_silently=False)],
    )

    @sd.field(
        description="Get a team by ID",
        extensions=[HasPerm("team.view", message="You don't have permission to view that team.")],
        deprecation_reason="Use the `teams` field instead.",
    )
    def team(self, team_id: sb.relay.GlobalID, info: sb.Info) -> Team:
        return roles_models.Team.objects.get(id=team_id.node_id)  # type: ignore[return-value]

    @sd.field(
        description="Get a team type by ID",
        extensions=[HasPerm("team_type.view", message="You don't have permission to view that team type.")],
        deprecation_reason="Use the `team_types` field instead.",
    )
    def team_type(self, team_type_id: sb.relay.GlobalID, info: sb.Info) -> TeamType:
        return roles_models.TeamType.objects.get(id=team_type_id.node_id)  # type: ignore[return-value]

    team_types: sd.relay.DjangoListConnection[TeamType] = sd.connection(
        description="List team types",
        extensions=[
            HasPerm("team_type.list", message="You don't have permission to list team types.", fail_silently=False)
        ],
    )

    @sd.field(
        description="Get a role by ID",
        extensions=[HasRetvalPerm("role.view", message="You don't have permission to view that role.")],
        deprecation_reason="Use the `roles` field instead.",
    )
    def role(self, role_id: sb.relay.GlobalID, info: sb.Info) -> Role:
        return roles_models.Role.objects.get(id=role_id.node_id)  # type: ignore[return-value]

    roles: sd.relay.DjangoListConnection[Role] = sd.connection(
        description="List roles",
        extensions=[HasPerm("role.list", message="You don't have permission to list roles.", fail_silently=False)],
    )

    @sd.field(
        description="Get an accreditation by ID",
        extensions=[
            HasRetvalPerm("accreditation.view", message="You don't have permission to view that accreditation.")
        ],
        deprecation_reason="Use the `accreditations` field instead.",
    )
    def accreditation(self, accreditation_id: sb.relay.GlobalID, info: sb.Info) -> Accreditation:
        return roles_models.Accreditation.objects.get(id=accreditation_id.node_id)  # type: ignore[return-value]

    accreditations: sd.relay.DjangoListConnection[Accreditation] = sd.connection(
        description="List accreditations",
        extensions=[
            HasPerm(
                "accreditation.list", message="You don't have permission to list accreditations.", fail_silently=False
            )
        ],
    )
