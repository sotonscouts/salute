from uuid import UUID

import pytest
from django.urls import reverse
from strawberry.relay import to_base64
from strawberry_django.test.client import Response, TestClient

from salute.accounts.models import User
from salute.roles.factories import RoleTypeFactory


@pytest.mark.django_db
class TestRoleTypeQuery:
    url = reverse("graphql")

    QUERY = """
    query getRoleType($roleTypeId: ID!) {
        roleType(roleTypeId: $roleTypeId) {
            id
            displayName
        }
    }
    """

    def test_query__not_authenticated(self) -> None:
        role_type = RoleTypeFactory()
        client = TestClient(self.url)
        results = client.query(
            self.QUERY,
            variables={"roleTypeId": to_base64("RoleType", role_type.id)},  # type: ignore[dict-item]
            assert_no_errors=False,
        )

        assert isinstance(results, Response)

        assert results.errors == [
            {
                "message": "You don't have permission to view that role type.",
                "locations": [{"line": 3, "column": 9}],
                "path": ["roleType"],
            }
        ]
        assert results.data is None

    def test_query__no_permission(self, user: User) -> None:
        role_type = RoleTypeFactory()
        client = TestClient(self.url)
        with client.login(user):
            results = client.query(
                self.QUERY,
                variables={"roleTypeId": to_base64("RoleType", role_type.id)},  # type: ignore[dict-item]
                assert_no_errors=False,
            )

        assert isinstance(results, Response)

        assert results.errors == [
            {
                "message": "You don't have permission to view that role type.",
                "locations": [{"line": 3, "column": 9}],
                "path": ["roleType"],
            }
        ]
        assert results.data is None

    def test_query(self, user_with_person: User) -> None:
        role_type = RoleTypeFactory()
        client = TestClient(self.url)
        with client.login(user_with_person):
            result = client.query(
                self.QUERY,
                variables={"roleTypeId": to_base64("RoleType", role_type.id)},  # type: ignore[dict-item]
            )

        assert isinstance(result, Response)

        assert result.errors is None
        assert result.data == {
            "roleType": {
                "id": to_base64("RoleType", role_type.id),
                "displayName": role_type.name,
            }
        }

    def test_query__not_found(self, user_with_person: User) -> None:
        client = TestClient(self.url)
        with client.login(user_with_person):
            result = client.query(
                self.QUERY,
                variables={"roleTypeId": to_base64("RoleType", UUID(int=0))},  # type: ignore[dict-item]
                assert_no_errors=False,
            )

        assert isinstance(result, Response)

        assert result.errors == [
            {
                "locations": [{"column": 9, "line": 3}],
                "message": "RoleType matching query does not exist.",
                "path": ["roleType"],
            }
        ]
        assert result.data is None
