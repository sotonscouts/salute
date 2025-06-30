import pytest
from django.urls import reverse
from strawberry.relay import to_base64
from strawberry_django.test.client import Response, TestClient

from salute.accounts.models import DistrictUserRole, DistrictUserRoleType, User
from salute.hierarchy.factories import DistrictFactory
from salute.roles.factories import DistrictTeamFactory, TeamTypeFactory


@pytest.mark.django_db
class TestTeamListQuery:
    url = reverse("graphql")

    QUERY = """
    query listTeams($filters: TeamFilter) {
        teams(filters: $filters) {
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

    def test_query__filter_by_id(self, user_with_person: User) -> None:
        district = DistrictFactory()
        DistrictUserRole.objects.create(user=user_with_person, district=district, level=DistrictUserRoleType.MANAGER)

        teams = DistrictTeamFactory.create_batch(size=5)
        client = TestClient(self.url)
        with client.login(user_with_person):
            result = client.query(
                self.QUERY,
                variables={"filters": {"id": {"inList": [to_base64("Team", team.id) for team in teams[:2]]}}},
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
                    for team in sorted(teams[:2], key=lambda team: team.team_type.name)
                ],
                "totalCount": 2,
            }
        }

    def test_query__filter_by_team_type(self, user_with_person: User) -> None:
        district = DistrictFactory()
        DistrictUserRole.objects.create(user=user_with_person, district=district, level=DistrictUserRoleType.MANAGER)

        DistrictTeamFactory.create_batch(size=5)
        team_type = TeamTypeFactory(name="Expected Team Type")
        expected_teams = DistrictTeamFactory.create_batch(size=2, team_type=team_type)
        client = TestClient(self.url)
        with client.login(user_with_person):
            result = client.query(
                self.QUERY,
                variables={"filters": {"teamType": {"id": {"exact": to_base64("TeamType", team_type.id)}}}},
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
                    for team in sorted(expected_teams, key=lambda team: team.team_type.name)
                ],
                "totalCount": 2,
            }
        }
