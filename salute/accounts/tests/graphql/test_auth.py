from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING, Any

import time_machine
from django.test import Client
from django.urls import reverse
from rest_framework_simplejwt.tokens import RefreshToken

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

    @time_machine.travel("2025-01-01T12:00:00")
    def test_valid_access_token(self, admin_user: User, client: Client) -> None:
        refresh_token = RefreshToken.for_user(admin_user)

        resp = self._query(client, headers={"authorization": f"Bearer {refresh_token.access_token}"})

        self._assert_allowed(resp)

    def test_invalid_access_token__expired(self, admin_user: User, client: Client) -> None:
        with time_machine.travel("2025-01-01T12:00:00"):
            refresh_token = RefreshToken.for_user(admin_user)
            access_token = str(refresh_token.access_token)

        with time_machine.travel("2025-01-01T12:05:01"):
            resp = self._query(client, headers={"authorization": f"Bearer {access_token}"})

            self._assert_unauthorized(resp)

    def test_invalid_access_token__before_issued(self, admin_user: User, client: Client) -> None:
        with time_machine.travel("2025-01-01T12:00:00"):
            refresh_token = RefreshToken.for_user(admin_user)
            access_token = str(refresh_token.access_token)

        with time_machine.travel("2025-01-01T11:00:00"):
            resp = self._query(client, headers={"authorization": f"Bearer {access_token}"})

            self._assert_unauthorized(resp)

    @time_machine.travel("2025-01-01T12:00:00")
    def test_invalid_access_token__user_inactive(self, admin_user: User, client: Client) -> None:
        refresh_token = RefreshToken.for_user(admin_user)
        access_token = str(refresh_token.access_token)

        admin_user.is_active = False
        admin_user.save()

        resp = self._query(client, headers={"authorization": f"Bearer {access_token}"})

        assert resp.status_code == HTTPStatus.UNAUTHORIZED
        data = resp.json()
        assert data == {
            "code": "authentication_failed",
            "detail": "authentication_failed",
        }

    @time_machine.travel("2025-01-01T12:00:00")
    def test_invalid_access_token__user_does_not_exist(self, admin_user: User, client: Client) -> None:
        refresh_token = RefreshToken.for_user(admin_user)
        access_token = str(refresh_token.access_token)

        admin_user.delete()

        resp = self._query(client, headers={"authorization": f"Bearer {access_token}"})

        assert resp.status_code == HTTPStatus.UNAUTHORIZED
        data = resp.json()
        assert data == {
            "code": "authentication_failed",
            "detail": "authentication_failed",
        }
