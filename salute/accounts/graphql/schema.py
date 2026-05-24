import strawberry
from strawberry_django.auth.utils import get_current_user

from salute.api.extensions import IsPersonOrHasScope
from salute.api.scopes import ApiScope

from .graph_types import User


@strawberry.type
class AccountsQuery:
    @strawberry.field(description="Get the current user", extensions=[IsPersonOrHasScope(ApiScope.USER_READ)])
    def current_user(self, info: strawberry.Info) -> User:
        user = get_current_user(info)
        assert user.is_authenticated
        return user  # type: ignore[return-value]
