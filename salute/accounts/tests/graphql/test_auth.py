from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING, Any

from django.test import Client
from django.urls import reverse

from salute.accounts.models import User

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

    def _assert_allowed(self, resp: _MonkeyPatchedWSGIResponse) -> None:
        data = resp.json()
        assert data.get("errors") is None
        assert data["data"] == {
            "currentUser": {
                "email": "admin@example.com",
            }
        }

    def _assert_not_allowed(
        self, resp: _MonkeyPatchedWSGIResponse, *, expected_status: HTTPStatus = HTTPStatus.OK
    ) -> None:
        assert resp.status_code == expected_status
        data = resp.json()
        assert data["errors"] == [
            {"message": "User is not authenticated.", "locations": [{"line": 3, "column": 9}], "path": ["currentUser"]}
        ]
        assert data["data"] is None

    def _assert_unauthorized(self, resp: _MonkeyPatchedWSGIResponse) -> None:
        """We get this response if the token is bad, returned by the middleware."""
        assert resp.status_code == HTTPStatus.UNAUTHORIZED
        data = resp.json()
        assert data == {
            "code": "token_not_valid",
            "detail": "token_not_valid",
            "messages": [
                {"message": "token_not_valid", "token_class": "token_not_valid", "token_type": "token_not_valid"}
            ],
        }

    def _query(self, client: Client, **kwargs: Any) -> _MonkeyPatchedWSGIResponse:
        return client.post(self.url, data={"query": self.CURRENT_USER_QUERY}, content_type="application/json", **kwargs)

    def test_not_authenticated(self, client: Client) -> None:
        resp = self._query(client)

        self._assert_not_allowed(resp)

    def test_session_auth(self, admin_user: User, client: Client) -> None:
        client.force_login(admin_user)

        resp = self._query(client)

        self._assert_allowed(resp)
