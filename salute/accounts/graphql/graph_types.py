from datetime import datetime
from typing import Annotated

import strawberry as sb
import strawberry_django as sd
from strawberry_django.auth.utils import get_current_user

from salute.accounts import models


@sb.type
class UserDistrictRole:
    level: models.DistrictUserRoleType


UserRole = Annotated[UserDistrictRole, sb.union("UserRole")]


@sd.type(models.User)
class User(sb.relay.Node):
    email: str = sb.field(description="Email address")
    last_login: datetime = sb.field(description="Timestamp of most recent login")

    @sd.field(description="Get the roles for the user", select_related=["district_roles"])
    def roles(self, info: sb.Info) -> list[UserRole]:
        user = get_current_user(info)
        if not user.is_authenticated:
            return []

        return [
            UserDistrictRole(level=role.level)
            for role in user.district_roles.all()  # type: ignore[attr-defined]
        ]


@sb.type
class LoginSuccess:
    user: User
    access_token: str
    refresh_token: str


@sb.type
class AuthError:
    message: str


@sb.type
class RevokeSuccess:
    success: bool = True


LoginResult = Annotated[LoginSuccess | AuthError, sb.union("LoginResult")]
RevokeResult = Annotated[RevokeSuccess | AuthError, sb.union("RevokeResult")]
