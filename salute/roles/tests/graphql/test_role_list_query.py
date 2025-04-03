from typing import Any

import pytest
from django.urls import reverse
from strawberry.relay import to_base64
from strawberry_django.test.client import Response, TestClient

from salute.accounts.models import DistrictUserRole, DistrictUserRoleType, User
from salute.hierarchy.factories import DistrictFactory
from salute.roles.factories import RoleFactory
from salute.roles.models import Role


@pytest.mark.django_db
class TestRoleListQuery:
    url = reverse("graphql")

    QUERY = """
    query listRoles($filters: RoleFilter) {
        roles(filters: $filters) {
            totalCount
            edges {
                node {
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
            assert_no_errors=False,
        )

        assert isinstance(results, Response)

        assert results.errors == [
            {
                "message": "You don't have permission to list roles.",
                "locations": [{"line": 3, "column": 9}],
                "path": ["roles"],
            }
        ]
        assert results.data is None

    def test_query__no_person(self, user: User) -> None:
        client = TestClient(self.url)
        with client.login(user):
            results = client.query(
                self.QUERY,
                assert_no_errors=False,
            )

        assert isinstance(results, Response)

        assert results.errors == [
            {
                "message": "You don't have permission to list roles.",
                "locations": [{"line": 3, "column": 9}],
                "path": ["roles"],
            }
        ]
        assert results.data is None

    def test_query__no_permission(self, user_with_person: User) -> None:
        RoleFactory()

        client = TestClient(self.url)
        with client.login(user_with_person):
            results = client.query(
                self.QUERY,
                assert_no_errors=False,
            )

        assert isinstance(results, Response)

        assert results.data == {"roles": {"totalCount": 0, "edges": []}}
        assert results.errors is None

    def test_query__just_own_roles(self, user_with_person: User) -> None:
        RoleFactory()
        role = RoleFactory(person=user_with_person.person)

        client = TestClient(self.url)
        with client.login(user_with_person):
            results = client.query(
                self.QUERY,
                assert_no_errors=False,
            )

        assert isinstance(results, Response)

        assert results.data == {
            "roles": {
                "totalCount": 1,
                "edges": [{"node": self._get_expected_data_for_role(role)}],
            }
        }
        assert results.errors is None

    def test_query(self, user_with_person: User) -> None:
        district = DistrictFactory()
        DistrictUserRole.objects.create(user=user_with_person, district=district, level=DistrictUserRoleType.MANAGER)

        roles = RoleFactory.create_batch(size=10, team__district=district)
        client = TestClient(self.url)
        with client.login(user_with_person):
            result = client.query(
                self.QUERY,
            )

        assert isinstance(result, Response)

        assert result.errors is None
        assert result.data == {
            "roles": {
                "edges": [
                    {"node": self._get_expected_data_for_role(role)}
                    for role in sorted(roles, key=lambda role: role.team.display_name)
                ],
                "totalCount": 10,
            }
        }

    @pytest.mark.parametrize(
        ("is_automatic",),
        [
            pytest.param(True, id="automatic"),
            pytest.param(False, id="not_automatic"),
        ],
    )
    def test_query__filter_is_automatic(self, user_with_person: User, *, is_automatic: bool) -> None:
        district = DistrictFactory()
        DistrictUserRole.objects.create(user=user_with_person, district=district, level=DistrictUserRoleType.MANAGER)

        expected_for_filter_val = {
            True: RoleFactory(status__name="-", team__district=district),
            False: RoleFactory(status__name="Full", team__district=district),
        }

        client = TestClient(self.url)
        with client.login(user_with_person):
            result = client.query(
                self.QUERY,
                variables={"filters": {"isAutomatic": is_automatic}},
            )

        assert isinstance(result, Response)

        assert result.errors is None
        assert result.data == {
            "roles": {
                "edges": [{"node": self._get_expected_data_for_role(expected_for_filter_val[is_automatic])}],
                "totalCount": 1,
            }
        }
