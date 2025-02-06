from http import HTTPStatus

from django.test import Client as DjangoTestClient
from django.test import override_settings
from django.urls import reverse
from strawberry_django.test.client import Response, TestClient

from salute.accounts.models import User


class TestSchema:
    PING_QUERY = """
    query {
        ping
    }
    """

    def test_ping__not_authenticated(self) -> None:
        client = TestClient("/graphql/")
        results = client.query(self.PING_QUERY, assert_no_errors=False)

        assert isinstance(results, Response)

        assert results.errors == [
            {"message": "User is not authenticated.", "locations": [{"line": 3, "column": 9}], "path": ["ping"]}
        ]
        assert results.data is None

    def test_ping__authenticated(self, admin_user: User) -> None:
        client = TestClient("/graphql/")
        with client.login(admin_user):
            result = client.query(self.PING_QUERY)

        assert isinstance(result, Response)

        assert result.errors is None
        assert result.data == {"ping": "pong"}
