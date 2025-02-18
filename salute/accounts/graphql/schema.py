import strawberry
import strawberry_django
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import update_last_login
from rest_framework_simplejwt.exceptions import TokenBackendError, TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from strawberry_django.auth.utils import get_current_user
from strawberry_django.permissions import IsAuthenticated

from salute.accounts import models as accounts_models

from .graph_types import AuthError, LoginResult, LoginSuccess, User


@strawberry.type
class AccountsQuery:
    @strawberry.field(description="Get the current user", extensions=[IsAuthenticated()])
    def current_user(self, info: strawberry.Info) -> User:
        user = get_current_user(info)
        assert user.is_authenticated
        return user  # type: ignore[return-value]


@strawberry.type
class AccountsMutation:
    @strawberry_django.field(description="Login with credentials.")
    def login_with_credentials(self, email: str, password: str) -> LoginResult:
        user = authenticate(username=email, password=password)
        if user is None:
            return AuthError(message="No active account found with the given credentials")

        update_last_login(None, user)  # type: ignore[arg-type]
        refresh_token = RefreshToken.for_user(user)

        return LoginSuccess(
            user=user,  # type: ignore[arg-type]
            access_token=str(refresh_token.access_token),
            refresh_token=str(refresh_token),
        )
