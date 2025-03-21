from __future__ import annotations

from typing import Any, Literal, TypedDict

import requests
from django.conf import settings

from salute.accounts.models import User
from salute.api.auth0.utils import Auth0TokenInfo, get_token_info
from salute.integrations.workspace.models import WorkspaceAccount


class RequestAuthenticationError(Exception):
    def __init__(self, errors: list[dict[Literal["message"], str]], *args: Any) -> None:
        self.errors = errors
        super().__init__(*args)


class UnableToLinkAccountError(Exception):
    """Exception raised when user account linking fails."""

    def __init__(self, reason: str, *args: Any) -> None:
        self.reason = reason
        super().__init__(*args)


class AuthInfo(TypedDict):
    user: User
    scopes: list[str]


def authenticate_user_with_bearer_token(token: str) -> AuthInfo:
    # Handle token validation errors
    try:
        token_info = get_token_info(token)
    except ValueError as e:
        raise RequestAuthenticationError(errors=[{"message": "Invalid access token"}]) from e
    except Exception as e:  # noqa: BLE001
        raise RequestAuthenticationError(errors=[{"message": "Server error during token validation"}]) from e

    # If the sub is missing, it could be blank. Reject blank subjects.
    if not token_info.sub:
        raise RequestAuthenticationError(errors=[{"message": "Invalid Access Token: Missing subject"}])

    # Check that the token has the required audience
    if token_info.aud != settings.AUTH0_AUDIENCE:  # type: ignore[misc]
        raise RequestAuthenticationError(
            errors=[{"message": "Invalid Access Token: Audience not valid for this service"}]
        )

    # Check if the token has the required scope
    if "salute:user" not in token_info.scopes:
        raise RequestAuthenticationError(errors=[{"message": "Insufficient permissions: 'salute:user' scope required"}])

    try:
        user = User.objects.get(auth0_sub=token_info.sub)
    except User.DoesNotExist:
        try:
            user = _attempt_to_link_user(token, token_info)
        except UnableToLinkAccountError as e:
            raise RequestAuthenticationError(errors=[{"message": f"Unable to link account: {e.reason}"}]) from e
        except Exception as e:  # noqa: BLE001
            raise RequestAuthenticationError(
                errors=[{"message": f"Unable to link account due to an unknown error: {e}"}]
            ) from None

    if not user.is_active:
        raise RequestAuthenticationError(errors=[{"message": "User account is inactive"}])

    if not user.person:
        raise RequestAuthenticationError(errors=[{"message": "User account is not linked to a person"}])

    if user.person.is_suspended:
        raise RequestAuthenticationError(errors=[{"message": "User account is linked to a suspended person"}])

    return AuthInfo(user=user, scopes=token_info.scopes)


def _attempt_to_link_user(token: str, token_info: Auth0TokenInfo) -> User:
    """
    Attempt to link an Auth0 user to a Person in the system.

    Args:
        token: The raw JWT token
        token_info: The decoded token information

    Returns:
        User: The newly created user

    Raises:
        UnableToLinkAccountError: If the account cannot be linked
    """
    # Check if this is a Google account
    google_id = token_info.get_google_uid()
    if not google_id:
        raise UnableToLinkAccountError(reason="Only Google accounts are supported")

    # Check for workspace account
    try:
        workspace_account = WorkspaceAccount.objects.get(google_id=google_id)
    except WorkspaceAccount.DoesNotExist:
        raise UnableToLinkAccountError(reason="Unknown Google Account") from None

    # Validate the workspace account
    if not workspace_account.person or workspace_account.person.is_suspended:
        raise UnableToLinkAccountError(reason="Account is not linked to an active person")

    if workspace_account.suspended or workspace_account.archived:
        raise UnableToLinkAccountError(reason="Google Account is deactivated")

    if User.objects.filter(person=workspace_account.person).exists():
        raise UnableToLinkAccountError(reason="Person is already linked to another user account")

    # Check if token has email scope and get user's email
    if "email" not in token_info.scopes:
        raise UnableToLinkAccountError(reason="Email scope is required for account creation")

    # Get email from userinfo endpoint
    try:
        resp = requests.get(
            f"https://{settings.AUTH0_DOMAIN}/userinfo",  # type: ignore[misc]
            headers={"Authorization": f"Bearer {token}"},
            timeout=5,
        )
        resp.raise_for_status()
        userinfo = resp.json()
    except (requests.RequestException, ValueError) as e:
        raise UnableToLinkAccountError(reason="Failed to fetch user info") from e

    email = userinfo.get("email")
    if not email:
        raise UnableToLinkAccountError(reason="Failed to fetch email for user")

    # Check if user with this email already exists
    if User.objects.filter(email=email).exists():
        raise UnableToLinkAccountError(reason="User with this email already exists")

    # Create the user
    user = User.objects.create(
        email=email,
        person=workspace_account.person,
        auth0_sub=token_info.sub,
    )

    return user
