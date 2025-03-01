import pytest
from django.urls import reverse
from strawberry_django.test.client import Response, TestClient

from salute.accounts.models import User


@pytest.mark.django_db
class TestGetRoleStatusesQuery:
    url = reverse("graphql")

    QUERY = """
    query {
        roleStatuses {
            displayName
        }
    }
    """

    def test_get_role_statuses_query__not_authenticated(self) -> None:
        client = TestClient(self.url)
        results = client.query(self.QUERY, assert_no_errors=False)

        assert isinstance(results, Response)

        assert results.errors == [
            {
                "message": "You don't have permission to list role statuses.",
                "locations": [{"line": 3, "column": 9}],
                "path": ["roleStatuses"],
            }
        ]
        assert results.data is None

    def test_get_role_statuses_query__no_permission(self, user: User) -> None:
        client = TestClient(self.url)
        with client.login(user):
            results = client.query(self.QUERY, assert_no_errors=False)

        assert isinstance(results, Response)

        assert results.errors == [
            {
                "message": "You don't have permission to list role statuses.",
                "locations": [{"line": 3, "column": 9}],
                "path": ["roleStatuses"],
            }
        ]
        assert results.data is None

    def test_get_role_statuses_query__cannot_query_private_fields(self, user_with_person: User) -> None:
        client = TestClient(self.url)
        with client.login(user_with_person):
            results = client.query(
                """
                query {
                    roleStatuses {
                        name
                    }
                }
            """,
                assert_no_errors=False,
            )

        assert isinstance(results, Response)

        assert results.errors == [
            {
                "message": "Cannot query field 'name' on type 'RoleStatus'.",
                "locations": [{"line": 4, "column": 25}],
            }
        ]
        assert results.data is None

    def test_get_role_statuses_query__none(self, user_with_person: User) -> None:
        client = TestClient(self.url)
        with client.login(user_with_person):
            result = client.query(self.QUERY)

        assert isinstance(result, Response)

        assert result.errors is None
        assert result.data == {"roleStatuses": []}
