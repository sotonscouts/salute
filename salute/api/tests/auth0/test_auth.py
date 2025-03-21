from __future__ import annotations

from unittest import mock

import pytest
import responses
from django.conf import settings

from salute.accounts.factories import UserFactory
from salute.api.auth0.auth import (
    RequestAuthenticationError,
    UnableToLinkAccountError,
    _attempt_to_link_user,
    authenticate_user_with_bearer_token,
)
from salute.api.auth0.types import Auth0TokenInfo
from salute.integrations.workspace.factories import WorkspaceAccountFactory
from salute.people.factories import PersonFactory

VALID_SCOPES = ["openid", "email", "salute:user"]
VALID_AUDIENCE = [settings.AUTH0_AUDIENCE]  # type: ignore[misc]


@pytest.mark.django_db
class TestAuth0TokenVerification:
    def test_bad_token_format(self) -> None:
        with pytest.raises(RequestAuthenticationError) as exc_info:
            authenticate_user_with_bearer_token("bees")
        assert exc_info.value.errors == [{"message": "Invalid access token"}]

    @mock.patch("salute.api.auth0.auth.get_token_info")
    def test_token_validation_raise_exception(self, mock_get_token_info: mock.Mock) -> None:
        mock_get_token_info.side_effect = Exception()

        with pytest.raises(RequestAuthenticationError) as exc_info:
            authenticate_user_with_bearer_token("bees")
        assert exc_info.value.errors == [{"message": "Server error during token validation"}]

    @mock.patch("salute.api.auth0.auth.get_token_info")
    def test_token_validation_empty_sub(self, mock_get_token_info: mock.Mock) -> None:
        mock_get_token_info.return_value = Auth0TokenInfo(sub="", scopes=VALID_SCOPES, aud=VALID_AUDIENCE)

        with pytest.raises(RequestAuthenticationError) as exc_info:
            authenticate_user_with_bearer_token("bees")
        assert exc_info.value.errors == [{"message": "Invalid Access Token: Missing subject"}]

    @mock.patch("salute.api.auth0.auth.get_token_info")
    def test_token_validation_invalid_audience(self, mock_get_token_info: mock.Mock) -> None:
        mock_get_token_info.return_value = Auth0TokenInfo(
            sub="subject", scopes=["openid", "email"], aud="invalid.example.com"
        )

        with pytest.raises(RequestAuthenticationError) as exc_info:
            authenticate_user_with_bearer_token("bees")
        assert exc_info.value.errors == [{"message": "Invalid Access Token: Audience not valid for this service"}]

    @mock.patch("salute.api.auth0.auth.get_token_info")
    def test_token_validation_missing_salute_user_scope(self, mock_get_token_info: mock.Mock) -> None:
        mock_get_token_info.return_value = Auth0TokenInfo(sub="subject", scopes=["openid", "email"], aud=VALID_AUDIENCE)

        with pytest.raises(RequestAuthenticationError) as exc_info:
            authenticate_user_with_bearer_token("bees")
        assert exc_info.value.errors == [{"message": "Insufficient permissions: 'salute:user' scope required"}]

    @mock.patch("salute.api.auth0.auth.get_token_info")
    def test_existing_user__inactive(self, mock_get_token_info: mock.Mock) -> None:
        person = PersonFactory(is_suspended=False)
        UserFactory(is_active=False, auth0_sub="1234", person=person)
        mock_get_token_info.return_value = Auth0TokenInfo(sub="1234", scopes=VALID_SCOPES, aud=VALID_AUDIENCE)

        with pytest.raises(RequestAuthenticationError) as exc_info:
            authenticate_user_with_bearer_token("bees")
        assert exc_info.value.errors == [{"message": "User account is inactive"}]

    @mock.patch("salute.api.auth0.auth.get_token_info")
    def test_existing_user__missing_person(self, mock_get_token_info: mock.Mock) -> None:
        UserFactory(auth0_sub="1234")
        mock_get_token_info.return_value = Auth0TokenInfo(sub="1234", scopes=VALID_SCOPES, aud=VALID_AUDIENCE)

        with pytest.raises(RequestAuthenticationError) as exc_info:
            authenticate_user_with_bearer_token("bees")
        assert exc_info.value.errors == [{"message": "User account is not linked to a person"}]

    @mock.patch("salute.api.auth0.auth.get_token_info")
    def test_existing_user__person_is_suspended(self, mock_get_token_info: mock.Mock) -> None:
        person = PersonFactory(is_suspended=True)
        UserFactory(auth0_sub="1234", person=person)
        mock_get_token_info.return_value = Auth0TokenInfo(sub="1234", scopes=VALID_SCOPES, aud=VALID_AUDIENCE)

        with pytest.raises(RequestAuthenticationError) as exc_info:
            authenticate_user_with_bearer_token("bees")
        assert exc_info.value.errors == [{"message": "User account is linked to a suspended person"}]

    @mock.patch("salute.api.auth0.auth.get_token_info")
    def test_existing_user__success(self, mock_get_token_info: mock.Mock) -> None:
        person = PersonFactory(is_suspended=False)
        user = UserFactory(auth0_sub="1234", person=person)
        mock_get_token_info.return_value = Auth0TokenInfo(sub="1234", scopes=VALID_SCOPES, aud=VALID_AUDIENCE)

        auth_info = authenticate_user_with_bearer_token("bees")

        assert auth_info["user"] == user
        assert auth_info["scopes"] == VALID_SCOPES

    @mock.patch("salute.api.auth0.auth._attempt_to_link_user")
    @mock.patch("salute.api.auth0.auth.get_token_info")
    def test_new_user_failed_to_link(
        self, mock_get_token_info: mock.Mock, mock_attempt_to_link_user: mock.Mock
    ) -> None:
        mock_get_token_info.return_value = Auth0TokenInfo(sub="1234", scopes=VALID_SCOPES, aud=VALID_AUDIENCE)
        mock_attempt_to_link_user.side_effect = UnableToLinkAccountError(reason="a reason")

        with pytest.raises(RequestAuthenticationError) as exc_info:
            authenticate_user_with_bearer_token("bees")
        assert exc_info.value.errors == [{"message": "Unable to link account: a reason"}]

    @mock.patch("salute.api.auth0.auth._attempt_to_link_user")
    @mock.patch("salute.api.auth0.auth.get_token_info")
    def test_new_user_successfully_linked(
        self, mock_get_token_info: mock.Mock, mock_attempt_to_link_user: mock.Mock
    ) -> None:
        person = PersonFactory(is_suspended=False)
        new_user = UserFactory(person=person)
        mock_get_token_info.return_value = Auth0TokenInfo(sub="1234", scopes=VALID_SCOPES, aud=VALID_AUDIENCE)
        mock_attempt_to_link_user.return_value = new_user

        auth_info = authenticate_user_with_bearer_token("bees")

        assert auth_info["user"] == new_user
        assert auth_info["scopes"] == VALID_SCOPES


@pytest.mark.django_db
class TestAuth0AttemptToLinkUser:
    def test_new_user__not_google_account_subject(self) -> None:
        token_info = Auth0TokenInfo(sub="subject", scopes=VALID_SCOPES, aud=VALID_AUDIENCE)

        with pytest.raises(UnableToLinkAccountError) as exc_info:
            _attempt_to_link_user("bees", token_info)
        assert exc_info.value.reason == "Only Google accounts are supported"

    def test_new_user__no_matching_workspace_account(self) -> None:
        token_info = Auth0TokenInfo(sub="google-oauth2|1234", scopes=VALID_SCOPES, aud=VALID_AUDIENCE)

        with pytest.raises(UnableToLinkAccountError) as exc_info:
            _attempt_to_link_user("bees", token_info)
        assert exc_info.value.reason == "Unknown Google Account"

    def test_new_user__unlinked_workspace_account(self) -> None:
        WorkspaceAccountFactory(google_id="1234")
        token_info = Auth0TokenInfo(sub="google-oauth2|1234", scopes=VALID_SCOPES, aud=VALID_AUDIENCE)

        with pytest.raises(UnableToLinkAccountError) as exc_info:
            _attempt_to_link_user("bees", token_info)
        assert exc_info.value.reason == "Account is not linked to an active person"

    def test_new_user__person_suspended(self) -> None:
        person = PersonFactory(is_suspended=True)
        WorkspaceAccountFactory(google_id="1234", person=person)
        token_info = Auth0TokenInfo(sub="google-oauth2|1234", scopes=VALID_SCOPES, aud=VALID_AUDIENCE)

        with pytest.raises(UnableToLinkAccountError) as exc_info:
            _attempt_to_link_user("bees", token_info)
        assert exc_info.value.reason == "Account is not linked to an active person"

    def test_new_user__account_suspended(self) -> None:
        person = PersonFactory(is_suspended=False)
        WorkspaceAccountFactory(google_id="1234", person=person, suspended=True)
        token_info = Auth0TokenInfo(sub="google-oauth2|1234", scopes=VALID_SCOPES, aud=VALID_AUDIENCE)

        with pytest.raises(UnableToLinkAccountError) as exc_info:
            _attempt_to_link_user("bees", token_info)
        assert exc_info.value.reason == "Google Account is deactivated"

    def test_new_user__account_archived(self) -> None:
        person = PersonFactory(is_suspended=False)
        WorkspaceAccountFactory(google_id="1234", person=person, archived=True)
        token_info = Auth0TokenInfo(sub="google-oauth2|1234", scopes=VALID_SCOPES, aud=VALID_AUDIENCE)

        with pytest.raises(UnableToLinkAccountError) as exc_info:
            _attempt_to_link_user("bees", token_info)
        assert exc_info.value.reason == "Google Account is deactivated"

    def test_new_user__person_already_linked(self) -> None:
        person = PersonFactory(is_suspended=False)
        UserFactory(person=person)
        WorkspaceAccountFactory(google_id="1234", person=person)
        token_info = Auth0TokenInfo(sub="google-oauth2|1234", scopes=VALID_SCOPES, aud=VALID_AUDIENCE)

        with pytest.raises(UnableToLinkAccountError) as exc_info:
            _attempt_to_link_user("bees", token_info)
        assert exc_info.value.reason == "Person is already linked to another user account"

    def test_new_user__missing_email_scope(self) -> None:
        person = PersonFactory(is_suspended=False)
        WorkspaceAccountFactory(google_id="1234", person=person)
        token_info = Auth0TokenInfo(sub="google-oauth2|1234", scopes=["openid", "salute:user"], aud=VALID_AUDIENCE)

        with pytest.raises(UnableToLinkAccountError) as exc_info:
            _attempt_to_link_user("bees", token_info)
        assert exc_info.value.reason == "Email scope is required for account creation"

    @mock.patch("salute.api.auth0.auth.requests.get")
    def test_new_user__failed_userinfo(self, mock_get: mock.Mock) -> None:
        person = PersonFactory(is_suspended=False)
        WorkspaceAccountFactory(google_id="1234", person=person)
        token_info = Auth0TokenInfo(sub="google-oauth2|1234", scopes=VALID_SCOPES, aud=VALID_AUDIENCE)
        mock_get.side_effect = ValueError("")

        with pytest.raises(UnableToLinkAccountError) as exc_info:
            _attempt_to_link_user("bees", token_info)
        assert exc_info.value.reason == "Failed to fetch user info"

    @responses.activate
    def test_new_user__missing_email(self) -> None:
        person = PersonFactory(is_suspended=False)
        WorkspaceAccountFactory(google_id="1234", person=person)
        token_info = Auth0TokenInfo(sub="google-oauth2|1234", scopes=VALID_SCOPES, aud=VALID_AUDIENCE)

        responses.get(
            f"https://{settings.AUTH0_DOMAIN}/userinfo",  # type: ignore[misc]
            headers={"Authorization": "Bearer bees"},
            json={},
            status=200,
        )

        with pytest.raises(UnableToLinkAccountError) as exc_info:
            _attempt_to_link_user("bees", token_info)
        assert exc_info.value.reason == "Failed to fetch email for user"

    @responses.activate
    def test_new_user__existing_email(self) -> None:
        existing_user = UserFactory()
        person = PersonFactory(is_suspended=False)
        WorkspaceAccountFactory(google_id="1234", person=person)
        token_info = Auth0TokenInfo(sub="google-oauth2|1234", scopes=VALID_SCOPES, aud=VALID_AUDIENCE)

        responses.get(
            f"https://{settings.AUTH0_DOMAIN}/userinfo",  # type: ignore[misc]
            headers={"Authorization": "Bearer bees"},
            json={"email": existing_user.email},
            status=200,
        )

        with pytest.raises(UnableToLinkAccountError) as exc_info:
            _attempt_to_link_user("bees", token_info)
        assert exc_info.value.reason == "User with this email already exists"

    @responses.activate
    def test_new_user__success(self) -> None:
        person = PersonFactory(is_suspended=False)
        WorkspaceAccountFactory(google_id="1234", person=person)
        token_info = Auth0TokenInfo(sub="google-oauth2|1234", scopes=VALID_SCOPES, aud=VALID_AUDIENCE)

        responses.get(
            f"https://{settings.AUTH0_DOMAIN}/userinfo",  # type: ignore[misc]
            headers={"Authorization": "Bearer bees"},
            json={"email": "user@example.com"},
            status=200,
        )

        user = _attempt_to_link_user("bees", token_info)
        assert user.email == "user@example.com"
        assert user.auth0_sub == "google-oauth2|1234"
        assert user.person == person
