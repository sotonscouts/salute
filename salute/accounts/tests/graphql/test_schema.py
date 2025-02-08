from django.urls import reverse
from strawberry_django.test.client import Response, TestClient

from salute.accounts.models import User


class TestGetCurrentUserQuery:
    url = reverse("graphql")

    CURRENT_USER_QUERY = """
    query {
        currentUser {
            email
            lastLogin
        }
    }
    """

    def test_current_user_query__not_authenticated(self) -> None:
        client = TestClient(self.url)
        results = client.query(self.CURRENT_USER_QUERY, assert_no_errors=False)

        assert isinstance(results, Response)

        assert results.errors == [
            {"message": "User is not authenticated.", "locations": [{"line": 3, "column": 9}], "path": ["currentUser"]}
        ]
        assert results.data is None

    def test_current_user_query__authenticated(self, admin_user: User) -> None:
        client = TestClient(self.url)
        with client.login(admin_user):
            result = client.query(self.CURRENT_USER_QUERY)

        assert admin_user.last_login
        assert isinstance(result, Response)

        assert result.errors is None
        assert result.data == {
            "currentUser": {
                "email": "admin@example.com",
                "lastLogin": admin_user.last_login.isoformat(),
            }
        }
