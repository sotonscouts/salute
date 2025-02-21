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

from .graph_types import AuthError, LoginResult, LoginSuccess, RevokeResult, RevokeSuccess, User


@strawberry.type
class AccountsQuery:
    @strawberry.field(description="Get the current user", extensions=[IsAuthenticated()])
    def current_user(self, info: strawberry.Info) -> User:
        user = get_current_user(info)
        assert user.is_authenticated
        return user  # type: ignore[return-value]


class NoValidUserError(Exception):
    pass


def _get_valid_user_for_refresh_token(refresh: RefreshToken) -> accounts_models.User:
    user_id = refresh.payload.get(settings.SIMPLE_JWT["USER_ID_CLAIM"], None)  # type: ignore[call-overload]
    try:
        return accounts_models.User.objects.filter(is_active=True).get(id=user_id)
    except accounts_models.User.DoesNotExist as e:
        raise NoValidUserError() from e


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

    @strawberry_django.field(description="Obtain a new access and refresh token. Refresh token will be rotated.")
    def refresh_token(self, refresh_token: str) -> LoginResult:
        try:
            refresh = RefreshToken(refresh_token)  # type: ignore[arg-type]
        except (TokenError, TokenBackendError):
            return AuthError(message="Refresh token was not valid")

        try:
            user = _get_valid_user_for_refresh_token(refresh)
        except NoValidUserError:
            return AuthError(message="No active account found with the given credentials")

        # Prevent the token from being used again
        refresh.blacklist()

        # Reset all token values, but keep existing claims
        refresh.set_jti()
        refresh.set_exp()
        refresh.set_iat()

        return LoginSuccess(
            user=user,  # type: ignore[arg-type]
            access_token=str(refresh.access_token),
            refresh_token=str(refresh),
        )

    @strawberry_django.field(description="Invalidate an existing refresh token.")
    def revoke_token(self, refresh_token: str) -> RevokeResult:
        try:
            refresh = RefreshToken(refresh_token)  # type: ignore[arg-type]
        except (TokenError, TokenBackendError):
            return AuthError(message="Refresh token was not valid")

        # Note: we do not need to check if the user is valid here, as the token is
        # going to be invalidated anyway, and we know the token is valid.

        # Prevent the token from being used again
        refresh.blacklist()

        return RevokeSuccess()
