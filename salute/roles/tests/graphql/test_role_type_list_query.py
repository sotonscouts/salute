import pytest
from django.urls import reverse
from strawberry.relay import to_base64
from strawberry_django.test.client import Response, TestClient

from salute.accounts.models import User
from salute.roles.factories import RoleTypeFactory


@pytest.mark.django_db
class TestRoleTypeListQuery:
    url = reverse("graphql")

    QUERY = """
    query listRoleTypes($filters: RoleTypeFilter) {
        roleTypes(filters: $filters) {
            edges {
                node {
                    id
                    displayName
                }
            }
            totalCount
        }
    }
    """

    def test_query__not_authenticated(self) -> None:
        client = TestClient(self.url)
        results = client.query(
            self.QUERY,
            assert_no_errors=False,
        )

        assert isinstance(results, Response)

        assert results.errors == [
            {
                "message": "You don't have permission to list role types.",
                "locations": [{"line": 3, "column": 9}],
                "path": ["roleTypes"],
            }
        ]
        assert results.data is None

    def test_query__no_permission(self, user: User) -> None:
        client = TestClient(self.url)
        with client.login(user):
            results = client.query(
                self.QUERY,
                assert_no_errors=False,
            )

        assert isinstance(results, Response)

        assert results.errors == [
            {
                "message": "You don't have permission to list role types.",
                "locations": [{"line": 3, "column": 9}],
                "path": ["roleTypes"],
            }
        ]
        assert results.data is None

    def test_query(self, user_with_person: User) -> None:
        role_types = RoleTypeFactory.create_batch(size=5)
        client = TestClient(self.url)
        with client.login(user_with_person):
            result = client.query(
                self.QUERY,
            )

        assert isinstance(result, Response)

        assert result.errors is None
        assert result.data == {
            "roleTypes": {
                "edges": [
                    {
                        "node": {
                            "id": to_base64("RoleType", rt.id),
                            "displayName": rt.name,
                        }
                    }
                    for rt in sorted(role_types, key=lambda rt: rt.name)
                ],
                "totalCount": 5,
            }
        }

    def test_query__filter__by_id(self, user_with_person: User) -> None:
        role_types = RoleTypeFactory.create_batch(size=5)
        expected_role_type = role_types[0]
        client = TestClient(self.url)
        with client.login(user_with_person):
            result = client.query(
                self.QUERY,
                variables={"filters": {"id": {"exact": to_base64("RoleType", expected_role_type.id)}}},
            )
        assert isinstance(result, Response)
        assert result.errors is None
        assert result.data == {
            "roleTypes": {
                "edges": [
                    {
                        "node": {
                            "id": to_base64("RoleType", expected_role_type.id),
                            "displayName": expected_role_type.name,
                        }
                    }
                ],
                "totalCount": 1,
            }
        }
