from typing import Any

import pytest
from django.urls import reverse
from strawberry.relay import to_base64
from strawberry_django.test.client import Response, TestClient

from salute.accounts.models import DistrictUserRole, DistrictUserRoleType, User
from salute.hierarchy.factories import DistrictFactory
from salute.people.factories import PersonFactory
from salute.roles.factories import RoleFactory
from salute.roles.models import Role


@pytest.mark.django_db
class TestRoleQuery:
    url = reverse("graphql")

    QUERY = """
    query getRole($id: GlobalID!) {
        role(roleId: $id) {
            id
            person {
                displayName
            }
            team {
                displayName
                unit {
                    displayName
                }
            }
            roleType {
                displayName
            }
            status {
                displayName
            }
        }
    }
    """

    def _get_expected_data_for_role(self, role: Role) -> dict[str, Any]:
        return {
            "id": to_base64("Role", role.id),
            "person": {
                "displayName": role.person.display_name,
            },
            "roleType": {
                "displayName": role.role_type.name,
            },
            "status": {
                "displayName": role.status.name,
            },
            "team": {
                "displayName": role.team.display_name,
                "unit": {
                    "displayName": role.team.unit.display_name,
                },
            },
        }

    def test_query__not_authenticated(self) -> None:
        client = TestClient(self.url)
        results = client.query(
            self.QUERY,
            variables={"id": "UGVyc29uTm9kZTox"},  # type: ignore[dict-item]
            assert_no_errors=False,
        )

        assert isinstance(results, Response)

        assert results.errors == [
            {
                "message": "You don't have permission to view that role.",
                "locations": [{"line": 3, "column": 9}],
                "path": ["role"],
            }
        ]
        assert results.data is None

    def test_query__no_person_associated_to_user(self, user: User) -> None:
        role = RoleFactory(team__district=DistrictFactory())
        client = TestClient(self.url)
        with client.login(user):
            results = client.query(
                self.QUERY,
                variables={"id": to_base64("Role", role.id)},  # type: ignore[dict-item]
                assert_no_errors=False,
            )

        assert isinstance(results, Response)

        assert results.errors == [
            {
                "message": "You don't have permission to view that role.",
                "locations": [{"line": 3, "column": 9}],
                "path": ["role"],
            }
        ]
        assert results.data is None

    def test_query__own_role(self, user_with_person: User) -> None:
        role = RoleFactory(person=user_with_person.person, team__district=DistrictFactory())
        client = TestClient(self.url)
        with client.login(user_with_person):
            results = client.query(
                self.QUERY,
                variables={"id": to_base64("Role", role.id)},  # type: ignore[dict-item]
            )

        assert isinstance(results, Response)

        assert results.errors is None
        assert results.data == {
            "role": self._get_expected_data_for_role(role),
        }

    def test_query__cannot_query_other_role(self, user_with_person: User) -> None:
        person = PersonFactory()
        role = RoleFactory(person=person, team__district=DistrictFactory())
        client = TestClient(self.url)
        with client.login(user_with_person):
            results = client.query(
                self.QUERY,
                variables={"id": to_base64("Role", role.id)},  # type: ignore[dict-item]
                assert_no_errors=False,
            )

        assert isinstance(results, Response)

        assert results.errors == [
            {
                "message": "You don't have permission to view that role.",
                "locations": [{"line": 3, "column": 9}],
                "path": ["role"],
            }
        ]
        assert results.data is None

    @pytest.mark.parametrize("role", DistrictUserRoleType)
    def test_query__role_can_query_other_role(self, role: DistrictUserRoleType, user_with_person: User) -> None:
        district = DistrictFactory()
        DistrictUserRole.objects.create(user=user_with_person, district=district, level=role)
        person = PersonFactory()
        role = RoleFactory(person=person, team__district=district)
        client = TestClient(self.url)
        with client.login(user_with_person):
            results = client.query(
                self.QUERY,
                variables={"id": to_base64("Role", role.id)},  # type: ignore[dict-item]
            )

        assert isinstance(results, Response)

        assert results.errors is None
        assert results.data == {
            "role": self._get_expected_data_for_role(role),
        }
