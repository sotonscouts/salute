import strawberry
from strawberry_django.auth.utils import get_current_user
from strawberry_django.permissions import IsAuthenticated

from .graph_types import User


@strawberry.type
class AccountsQuery:
    @strawberry.field(description="Get the current user", extensions=[IsAuthenticated()])
    def current_user(self, info: strawberry.Info) -> User:
        user = get_current_user(info)
        assert user.is_authenticated
        return user  # type: ignore[return-value]
