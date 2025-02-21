import pytest
import time_machine
from django.urls import reverse
from rest_framework_simplejwt.tokens import RefreshToken
from strawberry_django.test.client import Response, TestClient

from salute.accounts.factories import UserFactory


@pytest.mark.django_db
class TestRevokeTokenMutation:
    url = reverse("graphql")

    REVOKE_MUTATION = """
    mutation revoke($refreshToken: String!) {
        revokeToken(refreshToken: $refreshToken) {
            __typename

            ... on RevokeSuccess {
                success
            }

            ... on AuthError {
                message
            }
        }
    }
    """

    @time_machine.travel("2025-01-01T12:00:00")
    def test_revoke_mutation(self) -> None:
        user = UserFactory()

        rt = RefreshToken.for_user(user)
        token = str(rt)

        client = TestClient(self.url)
        results = client.query(self.REVOKE_MUTATION, variables={"refreshToken": token})  # type: ignore[dict-item]

        assert isinstance(results, Response)

        assert results.errors is None
        assert results.data == {"revokeToken": {"__typename": "RevokeSuccess", "success": True}}

    def test_revoke_mutation__no_such_account(self) -> None:
        user = UserFactory()

        rt = RefreshToken.for_user(user)
        token = str(rt)
        user.delete()

        client = TestClient(self.url)
        results = client.query(self.REVOKE_MUTATION, variables={"refreshToken": token})  # type: ignore[dict-item]

        assert isinstance(results, Response)

        assert results.errors is None
        assert results.data == {"revokeToken": {"__typename": "RevokeSuccess", "success": True}}

    def test_revoke_mutation__account_inactive(self) -> None:
        user = UserFactory(is_active=False)

        rt = RefreshToken.for_user(user)
        token = str(rt)

        client = TestClient(self.url)
        results = client.query(self.REVOKE_MUTATION, variables={"refreshToken": token})  # type: ignore[dict-item]

        assert isinstance(results, Response)

        assert results.errors is None
        assert results.data == {"revokeToken": {"__typename": "RevokeSuccess", "success": True}}

    def test_revoke_mutation__token_expired(self) -> None:
        user = UserFactory()

        with time_machine.travel("2025-01-01T12:00:00"):
            refresh_token = RefreshToken.for_user(user)
            token = str(refresh_token)

        with time_machine.travel("2025-01-01T14:00:01"):
            client = TestClient(self.url)
            results = client.query(self.REVOKE_MUTATION, variables={"refreshToken": token})  # type: ignore[dict-item]

        assert isinstance(results, Response)

        assert results.errors is None
        assert results.data == {
            "revokeToken": {
                "__typename": "AuthError",
                "message": "Refresh token was not valid",
            }
        }

    def test_revoke_mutation__token_denylist(self) -> None:
        user = UserFactory()

        refresh_token = RefreshToken.for_user(user)
        token = str(refresh_token)

        refresh_token.blacklist()

        client = TestClient(self.url)
        results = client.query(self.REVOKE_MUTATION, variables={"refreshToken": token})  # type: ignore[dict-item]

        assert isinstance(results, Response)

        assert results.errors is None
        assert results.data == {
            "revokeToken": {
                "__typename": "AuthError",
                "message": "Refresh token was not valid",
            }
        }

    def test_revoke_mutation__token_denylist_e2e(self) -> None:
        user = UserFactory()

        refresh_token = RefreshToken.for_user(user)
        token = str(refresh_token)

        client = TestClient(self.url)

        # Twice. The first time the token is valid, the second time it's denylisted
        _ = client.query(self.REVOKE_MUTATION, variables={"refreshToken": token})  # type: ignore[dict-item]
        results = client.query(self.REVOKE_MUTATION, variables={"refreshToken": token})  # type: ignore[dict-item]

        assert isinstance(results, Response)

        assert results.errors is None
        assert results.data == {
            "revokeToken": {
                "__typename": "AuthError",
                "message": "Refresh token was not valid",
            }
        }
