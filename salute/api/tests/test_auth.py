from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING, Any
from unittest import mock

from django.test import Client
from django.urls import reverse

from salute.accounts.models import User
from salute.api.auth0.auth import AuthInfo, RequestAuthenticationError

if TYPE_CHECKING:
    from django.test.client import _MonkeyPatchedWSGIResponse


class TestAPIAuthentication:
    url = reverse("graphql")

    CURRENT_USER_QUERY = """
    query {
        currentUser {
            email
        }
    }
    """

    def _query(self, client: Client, **kwargs: Any) -> _MonkeyPatchedWSGIResponse:
        return client.post(self.url, data={"query": self.CURRENT_USER_QUERY}, content_type="application/json", **kwargs)

    def test_not_authenticated(self, client: Client) -> None:
        resp = self._query(client)

        assert resp.status_code == HTTPStatus.OK
        data = resp.json()
        assert data["errors"] == [
            {"message": "User is not authenticated.", "locations": [{"line": 3, "column": 9}], "path": ["currentUser"]}
        ]
        assert data["data"] is None

    def test_session_auth(self, admin_user: User, client: Client) -> None:
        client.force_login(admin_user)

        resp = self._query(client)

        data = resp.json()
        assert data.get("errors") is None
        assert data["data"] == {
            "currentUser": {
                "email": "admin@example.com",
            }
        }

    @mock.patch("salute.api.views.authenticate_user_with_bearer_token")
    def test_auth0_auth(self, mock_auth: mock.Mock, admin_user: User, client: Client) -> None:
        mock_auth.return_value = AuthInfo(user=admin_user, scopes=["salute:user"])

        resp = self._query(client, headers={"Authorization": "Bearer token"})

        data = resp.json()
        assert data.get("errors") is None
        assert data["data"] == {
            "currentUser": {
                "email": "admin@example.com",
            }
        }

    @mock.patch("salute.api.views.authenticate_user_with_bearer_token")
    def test_auth0_failed(self, mock_auth: mock.Mock, admin_user: User, client: Client) -> None:
        mock_auth.side_effect = RequestAuthenticationError(errors=[{"message": "bad token"}])

        resp = self._query(client, headers={"Authorization": "Bearer token"})

        assert resp.status_code == HTTPStatus.OK

        data = resp.json()
        assert data["errors"] == [{"message": "bad token"}]
        assert data["data"] is None
