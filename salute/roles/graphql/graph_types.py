from __future__ import annotations

import strawberry as sb
import strawberry_django as sd

from salute.roles import models


@sd.type(models.TeamType)
class TeamType(sb.relay.Node):
    name: sb.Private[str]

    @sd.field(description="Formatted name for the team type", only="name")
    def display_name(self, info: sb.Info) -> str:
        return self.name


@sd.type(models.RoleType)
class RoleType(sb.relay.Node):
    name: sb.Private[str]

    @sd.field(description="Formatted name for the role type", only="name")
    def display_name(self, info: sb.Info) -> str:
        return self.name
