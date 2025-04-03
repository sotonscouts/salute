import pytest
from django.urls import reverse
from strawberry.relay import to_base64
from strawberry_django.test.client import Response, TestClient

from salute.accounts.models import DistrictUserRole, DistrictUserRoleType, User
from salute.hierarchy.factories import DistrictFactory
from salute.roles.factories import RoleFactory


@pytest.mark.django_db
class TestRoleListQuery:
    url = reverse("graphql")

    QUERY = """
    query {
        roles {
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
                "edges": [
                    {
                        "node": {
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
                                    "displayName": role.team.district.display_name,
                                },
                            },
                        }
                    }
                ],
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
                    {
                        "node": {
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
                                    "displayName": role.team.district.display_name,
                                },
                            },
                        }
                    }
                    for role in sorted(roles, key=lambda role: role.team.display_name)
                ],
                "totalCount": 10,
            }
        }
