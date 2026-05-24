from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING
from unittest import mock

import pytest
from django.test import Client
from django.urls import reverse

from salute.accounts.factories import ServiceAccountFactory, UserFactory
from salute.accounts.models import User
from salute.api.auth0.auth import AuthInfo, RequestAuthenticationError
from salute.api.scopes import ApiScope

if TYPE_CHECKING:
    from django.test.client import _MonkeyPatchedWSGIResponse

GRAPHQL_URL = reverse("graphql")
PING_QUERY = """
query {
    ping
}
"""


class TestAPIAuthentication:
    def _post(self, client: Client, **kwargs: object) -> _MonkeyPatchedWSGIResponse:
        return client.post(
            GRAPHQL_URL,
            data={"query": PING_QUERY},
            content_type="application/json",
            **kwargs,
        )

    def test_not_authenticated(self, client: Client) -> None:
        resp = self._post(client)

        assert resp.status_code == HTTPStatus.OK
        data = resp.json()
        assert data["errors"] == [
            {"message": "User is not authenticated.", "locations": [{"line": 3, "column": 5}], "path": ["ping"]}
        ]
        assert data["data"] is None

    @pytest.mark.django_db
    @mock.patch("salute.api.views.authenticate_user_with_bearer_token")
    def test_bearer_token_authenticates_request(self, mock_auth: mock.Mock, admin_user: User, client: Client) -> None:
        mock_auth.return_value = AuthInfo(user=admin_user, scopes=[ApiScope.SALUTE_USER])

        resp = self._post(client, headers={"Authorization": "Bearer token"})

        data = resp.json()
        assert data.get("errors") is None
        assert data["data"] == {"ping": "pong"}
        mock_auth.assert_called_once_with("token")

    @pytest.mark.django_db
    def test_service_account_session_rejected(self, client: Client) -> None:
        user = UserFactory(person=None, service_account=ServiceAccountFactory())
        client.force_login(user)

        resp = self._post(client)

        data = resp.json()
        assert data["errors"] == [{"message": "Service accounts must authenticate with a bearer token"}]
        assert data["data"] is None

    @mock.patch("salute.api.views.authenticate_user_with_bearer_token")
    def test_bearer_token_rejected(self, mock_auth: mock.Mock, client: Client) -> None:
        mock_auth.side_effect = RequestAuthenticationError(errors=[{"message": "bad token"}])

        resp = self._post(client, headers={"Authorization": "Bearer token"})

        assert resp.status_code == HTTPStatus.OK
        data = resp.json()
        assert data["errors"] == [{"message": "bad token"}]
        assert data["data"] is None
