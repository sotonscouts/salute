from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Annotated

import strawberry as sb
import strawberry_django as sd
from strawberry_django.auth.utils import get_current_user

from salute.accounts import models

if TYPE_CHECKING:
    from salute.people.graphql.graph_types import Person


@sb.type
class UserDistrictRole:
    level: models.DistrictUserRoleType


UserRole = Annotated[UserDistrictRole, sb.union("UserRole")]


@sd.type(models.User)
class User(sb.relay.Node):
    person: Annotated[Person, sb.lazy("salute.people.graphql.graph_types")] | None = sd.field(
        description="Person associated with the user"
    )  # noqa: E501
    email: str = sb.field(description="Email address")
    last_login: datetime = sb.field(description="Timestamp of most recent login")

    @sd.field(description="Get the roles for the user", select_related=["district_roles"])
    def user_roles(self, info: sb.Info) -> list[UserRole]:
        user = get_current_user(info)
        if not user.is_authenticated:
            return []

        return [
            UserDistrictRole(level=role.level)
            for role in user.district_roles.all()  # type: ignore[attr-defined]
        ]
