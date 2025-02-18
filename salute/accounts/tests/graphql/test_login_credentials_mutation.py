import zoneinfo
from datetime import datetime, timedelta

import pytest
import time_machine
from django.conf import Settings
from django.urls import reverse
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from strawberry_django.test.client import Response, TestClient

from salute.accounts.factories import UserFactory


@pytest.mark.django_db
class TestLoginWithCredentialsMutation:
    url = reverse("graphql")

    LOGIN_MUTATION = """
    mutation login($email: String!, $password: String!) {
        loginWithCredentials(email: $email, password: $password) {
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
    def test_login_mutation(self) -> None:
        previous_login_dt = datetime(2020, 1, 1, 12, 0, 0, tzinfo=zoneinfo.ZoneInfo("UTC"))
        user = UserFactory(last_login=previous_login_dt)
        user.set_password("password")
        user.save()

        client = TestClient(self.url)
        results = client.query(self.LOGIN_MUTATION, variables={"email": user.email, "password": "password"})  # type: ignore[dict-item]

        assert isinstance(results, Response)

        assert results.errors is None
        assert results.data == {"loginWithCredentials": {"__typename": "LoginSuccess", "user": {"email": user.email}}}

        # Check that the last login was bumped
        user.refresh_from_db()
        assert user.last_login != previous_login_dt

    @time_machine.travel("2025-01-01T12:00:00")
    def test_login_mutation__token(self, settings: Settings) -> None:
        user = UserFactory()
        user.set_password("password")
        user.save()

        client = TestClient(self.url)
        results = client.query(
            """
            mutation login($email: String!, $password: String!) {
                loginWithCredentials(email: $email, password: $password) {
                    __typename

                    ... on LoginSuccess {
                        accessToken
                        refreshToken
                    }
                }
            }
            """,
            variables={"email": user.email, "password": "password"},  # type: ignore[dict-item]
        )

        assert isinstance(results, Response)

        assert results.errors is None
        assert results.data["loginWithCredentials"]["__typename"] == "LoginSuccess"  # type: ignore[index]
        assert isinstance(results.data["loginWithCredentials"], dict)  # type: ignore[index]
        assert results.data["loginWithCredentials"].keys() == {"__typename", "accessToken", "refreshToken"}  # type: ignore[index]

        access_token: str = results.data["loginWithCredentials"]["accessToken"]  # type: ignore[index]
        refresh_token: str = results.data["loginWithCredentials"]["refreshToken"]  # type: ignore[index]

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

    def test_login_mutation__no_such_account(self) -> None:
        client = TestClient(self.url)
        results = client.query(self.LOGIN_MUTATION, variables={"email": "user@example.com", "password": "password"})  # type: ignore[dict-item]

        assert isinstance(results, Response)

        assert results.errors is None
        assert results.data == {
            "loginWithCredentials": {
                "__typename": "AuthError",
                "message": "No active account found with the given credentials",
            }
        }

    def test_login_mutation__wrong_password(self) -> None:
        user = UserFactory()
        user.set_password("secret1234")
        user.save()

        client = TestClient(self.url)
        results = client.query(self.LOGIN_MUTATION, variables={"email": user.email, "password": "password"})  # type: ignore[dict-item]

        assert isinstance(results, Response)

        assert results.errors is None
        assert results.data == {
            "loginWithCredentials": {
                "__typename": "AuthError",
                "message": "No active account found with the given credentials",
            }
        }

    def test_login_mutation__inactive_account(self) -> None:
        user = UserFactory(is_active=False)
        user.set_password("password")
        user.save()

        client = TestClient(self.url)
        results = client.query(self.LOGIN_MUTATION, variables={"email": user.email, "password": "password"})  # type: ignore[dict-item]

        assert isinstance(results, Response)

        assert results.errors is None
        assert results.data == {
            "loginWithCredentials": {
                "__typename": "AuthError",
                "message": "No active account found with the given credentials",
            }
        }
