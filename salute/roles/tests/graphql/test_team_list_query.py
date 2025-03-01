import pytest
from django.urls import reverse
from strawberry.relay import to_base64
from strawberry_django.test.client import Response, TestClient

from salute.accounts.models import DistrictUserRole, DistrictUserRoleType, User
from salute.hierarchy.factories import DistrictFactory
from salute.roles.factories import DistrictTeamFactory


@pytest.mark.django_db
class TestTeamTypeListQuery:
    url = reverse("graphql")

    QUERY = """
    query {
        teams {
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
                "message": "You don't have permission to list teams.",
                "locations": [{"line": 3, "column": 9}],
                "path": ["teams"],
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
                "message": "You don't have permission to list teams.",
                "locations": [{"line": 3, "column": 9}],
                "path": ["teams"],
            }
        ]
        assert results.data is None

    def test_query__no_permission(self, user_with_person: User) -> None:
        client = TestClient(self.url)
        with client.login(user_with_person):
            results = client.query(
                self.QUERY,
                assert_no_errors=False,
            )

        assert isinstance(results, Response)

        assert results.errors == [
            {
                "message": "You don't have permission to list teams.",
                "locations": [{"line": 3, "column": 9}],
                "path": ["teams"],
            }
        ]
        assert results.data is None

    def test_query(self, user_with_person: User) -> None:
        district = DistrictFactory()
        DistrictUserRole.objects.create(user=user_with_person, district=district, level=DistrictUserRoleType.MANAGER)

        teams = DistrictTeamFactory.create_batch(size=5)
        client = TestClient(self.url)
        with client.login(user_with_person):
            result = client.query(
                self.QUERY,
            )

        assert isinstance(result, Response)

        assert result.errors is None
        assert result.data == {
            "teams": {
                "edges": [
                    {
                        "node": {
                            "id": to_base64("Team", team.id),
                            "displayName": team.display_name,
                        }
                    }
                    for team in sorted(teams, key=lambda team: team.team_type.name)
                ],
                "totalCount": 5,
            }
        }
