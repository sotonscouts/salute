import zoneinfo
from datetime import datetime, timedelta

import pytest
import time_machine
from django.conf import Settings
from django.urls import reverse
from rest_framework_simplejwt.authentication import JWTAuthentication, TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from strawberry_django.test.client import Response, TestClient

from salute.accounts.factories import UserFactory


@pytest.mark.django_db
class TestRefreshTokenMutation:
    url = reverse("graphql")

    REFRESH_MUTATION = """
    mutation refresh($refreshToken: String!) {
        refreshToken(refreshToken: $refreshToken) {
            __typename

            ... on LoginSuccess {
                user {
                    email
                }
            }

            ... on AuthError {
                message
            }
        }
    }
    """

    @time_machine.travel("2025-01-01T12:00:00")
    def test_refresh_mutation(self) -> None:
        user = UserFactory()

        rt = RefreshToken.for_user(user)
        token = str(rt)

        client = TestClient(self.url)
        results = client.query(self.REFRESH_MUTATION, variables={"refreshToken": token})  # type: ignore[dict-item]

        assert isinstance(results, Response)

        assert results.errors is None
        assert results.data == {"refreshToken": {"__typename": "LoginSuccess", "user": {"email": user.email}}}

    @time_machine.travel("2025-01-01T12:00:00")
    def test_refresh_mutation__tokens(self, settings: Settings) -> None:
        user = UserFactory()

        rt = RefreshToken.for_user(user)
        token = str(rt)

        client = TestClient(self.url)
        results = client.query(
            """
            mutation refresh($refreshToken: String!) {
                refreshToken(refreshToken: $refreshToken) {
                    __typename

                    ... on LoginSuccess {
                        accessToken
                        refreshToken
                    }
                }
            }
            """,
            variables={"refreshToken": token},  # type: ignore[dict-item]
        )

        assert isinstance(results, Response)

        assert results.errors is None
        assert results.data["refreshToken"]["__typename"] == "LoginSuccess"  # type: ignore[index]
        assert isinstance(results.data["refreshToken"], dict)  # type: ignore[index]
        assert results.data["refreshToken"].keys() == {"__typename", "accessToken", "refreshToken"}  # type: ignore[index]

        access_token: str = results.data["refreshToken"]["accessToken"]  # type: ignore[index]
        refresh_token: str = results.data["refreshToken"]["refreshToken"]  # type: ignore[index]

        expected_issue_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=zoneinfo.ZoneInfo("UTC"))
        expected_access_expiry_time = expected_issue_time + timedelta(minutes=5)
        expected_refresh_expiry_time = expected_issue_time + timedelta(hours=2)

        jwt_auth = JWTAuthentication()
        access_token_data = jwt_auth.get_validated_token(access_token.encode())
        assert access_token_data["token_type"] == "access"  # noqa: S105
        assert access_token_data["exp"] == expected_access_expiry_time.timestamp()
        assert access_token_data["iat"] == expected_issue_time.timestamp()
        assert access_token_data["uid"] == user.id

        refresh_token_data = RefreshToken(refresh_token.encode())
        assert refresh_token_data["token_type"] == "refresh"  # noqa: S105
        assert refresh_token_data["exp"] == expected_refresh_expiry_time.timestamp()
        assert refresh_token_data["iat"] == expected_issue_time.timestamp()
        assert refresh_token_data["uid"] == user.id

        # Ensure the new refresh token is different from the old one
        assert refresh_token_data.payload["jti"] != rt.payload["jti"]

        # Ensure the old token is denylisted
        with pytest.raises(TokenError):
            rt.check_blacklist()

    def test_login_mutation__no_such_account(self) -> None:
        user = UserFactory()

        rt = RefreshToken.for_user(user)
        token = str(rt)
        user.delete()

        client = TestClient(self.url)
        results = client.query(self.REFRESH_MUTATION, variables={"refreshToken": token})  # type: ignore[dict-item]

        assert isinstance(results, Response)

        assert results.errors is None
        assert results.data == {
            "refreshToken": {
                "__typename": "AuthError",
                "message": "No active account found with the given credentials",
            }
        }

    def test_login_mutation__account_inactive(self) -> None:
        user = UserFactory(is_active=False)

        rt = RefreshToken.for_user(user)
        token = str(rt)

        client = TestClient(self.url)
        results = client.query(self.REFRESH_MUTATION, variables={"refreshToken": token})  # type: ignore[dict-item]

        assert isinstance(results, Response)

        assert results.errors is None
        assert results.data == {
            "refreshToken": {
                "__typename": "AuthError",
                "message": "No active account found with the given credentials",
            }
        }

    def test_login_mutation__token_expired(self) -> None:
        user = UserFactory()

        with time_machine.travel("2025-01-01T12:00:00"):
            refresh_token = RefreshToken.for_user(user)
            token = str(refresh_token)

        with time_machine.travel("2025-01-01T14:00:01"):
            client = TestClient(self.url)
            results = client.query(self.REFRESH_MUTATION, variables={"refreshToken": token})  # type: ignore[dict-item]

        assert isinstance(results, Response)

        assert results.errors is None
        assert results.data == {
            "refreshToken": {
                "__typename": "AuthError",
                "message": "Refresh token was not valid",
            }
        }

    def test_login_mutation__token_denylist(self) -> None:
        user = UserFactory()

        refresh_token = RefreshToken.for_user(user)
        token = str(refresh_token)

        refresh_token.blacklist()

        client = TestClient(self.url)
        results = client.query(self.REFRESH_MUTATION, variables={"refreshToken": token})  # type: ignore[dict-item]

        assert isinstance(results, Response)

        assert results.errors is None
        assert results.data == {
            "refreshToken": {
                "__typename": "AuthError",
                "message": "Refresh token was not valid",
            }
        }

    def test_login_mutation__token_denylist_e2e(self) -> None:
        user = UserFactory()

        refresh_token = RefreshToken.for_user(user)
        token = str(refresh_token)

        client = TestClient(self.url)

        # Twice. The first time the token is valid, the second time it's denylisted
        _ = client.query(self.REFRESH_MUTATION, variables={"refreshToken": token})  # type: ignore[dict-item]
        results = client.query(self.REFRESH_MUTATION, variables={"refreshToken": token})  # type: ignore[dict-item]

        assert isinstance(results, Response)

        assert results.errors is None
        assert results.data == {
            "refreshToken": {
                "__typename": "AuthError",
                "message": "Refresh token was not valid",
            }
        }
