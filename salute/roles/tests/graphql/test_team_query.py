from uuid import UUID

import pytest
from django.urls import reverse
from strawberry.relay import to_base64
from strawberry_django.test.client import Response, TestClient

from salute.accounts.models import DistrictUserRole, DistrictUserRoleType, User
from salute.hierarchy.factories import DistrictFactory
from salute.roles.factories import (
    DistrictTeamFactory,
    GroupSectionTeamFactory,
    GroupSubTeamFactory,
    GroupTeamFactory,
    TeamFactory,
)


@pytest.mark.django_db
class TestTeamTypeQuery:
    url = reverse("graphql")

    QUERY = """
    query getTeam($teamId: GlobalID!) {
        team(teamId: $teamId) {
            id
            displayName
            teamType {
                displayName
            }
            district {
                displayName
            }
            group {
                displayName
            }
            section {
                displayName
            }
            parentTeam {
                displayName
            }
            subTeams {
                displayName
            }
        }
    }
    """

    def test_query__not_authenticated(self) -> None:
        team = GroupSectionTeamFactory()
        client = TestClient(self.url)
        results = client.query(
            self.QUERY,
            variables={"teamId": to_base64("Team", team.id)},  # type: ignore[dict-item]
            assert_no_errors=False,
        )

        assert isinstance(results, Response)

        assert results.errors == [
            {
                "message": "You don't have permission to view that team.",
                "locations": [{"line": 3, "column": 9}],
                "path": ["team"],
            }
        ]
        assert results.data is None

    def test_query__no_person(self, user: User) -> None:
        team = GroupSectionTeamFactory()
        client = TestClient(self.url)
        with client.login(user):
            results = client.query(
                self.QUERY,
                variables={"teamId": to_base64("Team", team.id)},  # type: ignore[dict-item]
                assert_no_errors=False,
            )

        assert isinstance(results, Response)

        assert results.errors == [
            {
                "message": "You don't have permission to view that team.",
                "locations": [{"line": 3, "column": 9}],
                "path": ["team"],
            }
        ]
        assert results.data is None

    def test_query__not_found(self, user_with_person: User) -> None:
        district = DistrictFactory()
        DistrictUserRole.objects.create(user=user_with_person, district=district, level=DistrictUserRoleType.MANAGER)

        client = TestClient(self.url)
        with client.login(user_with_person):
            result = client.query(
                self.QUERY,
                variables={"teamId": to_base64("Team", UUID(int=0))},  # type: ignore[dict-item]
                assert_no_errors=False,
            )

        assert isinstance(result, Response)

        assert result.errors == [
            {
                "locations": [{"column": 9, "line": 3}],
                "message": "Team matching query does not exist.",
                "path": ["team"],
            }
        ]
        assert result.data is None

    def test_query__district_team(self, user_with_person: User) -> None:
        district = DistrictFactory()
        DistrictUserRole.objects.create(user=user_with_person, district=district, level=DistrictUserRoleType.MANAGER)

        team = DistrictTeamFactory(district=district)
        client = TestClient(self.url)
        with client.login(user_with_person):
            result = client.query(
                self.QUERY,
                variables={"teamId": to_base64("Team", team.id)},  # type: ignore[dict-item]
            )

        assert isinstance(result, Response)

        assert result.errors is None
        assert result.data == {
            "team": {
                "id": to_base64("Team", team.id),
                "displayName": team.display_name,
                "district": {"displayName": district.display_name},
                "parentTeam": None,
                "group": None,
                "section": None,
                "subTeams": [],
                "teamType": {"displayName": team.team_type.name},
            }
        }

    def test_query__group_team(self, user_with_person: User) -> None:
        district = DistrictFactory()
        DistrictUserRole.objects.create(user=user_with_person, district=district, level=DistrictUserRoleType.MANAGER)

        team = GroupTeamFactory()
        client = TestClient(self.url)
        with client.login(user_with_person):
            result = client.query(
                self.QUERY,
                variables={"teamId": to_base64("Team", team.id)},  # type: ignore[dict-item]
            )

        assert isinstance(result, Response)

        assert result.errors is None
        assert result.data == {
            "team": {
                "id": to_base64("Team", team.id),
                "displayName": team.display_name,
                "district": None,
                "parentTeam": None,
                "group": {
                    "displayName": team.group.display_name,
                },
                "section": None,
                "subTeams": [],
                "teamType": {"displayName": team.team_type.name},
            }
        }

    def test_query__section_team(self, user_with_person: User) -> None:
        district = DistrictFactory()
        DistrictUserRole.objects.create(user=user_with_person, district=district, level=DistrictUserRoleType.MANAGER)

        team = GroupSectionTeamFactory()
        client = TestClient(self.url)
        with client.login(user_with_person):
            result = client.query(
                self.QUERY,
                variables={"teamId": to_base64("Team", team.id)},  # type: ignore[dict-item]
            )

        assert isinstance(result, Response)

        assert result.errors is None
        assert result.data == {
            "team": {
                "id": to_base64("Team", team.id),
                "displayName": team.display_name,
                "district": None,
                "parentTeam": None,
                "group": None,
                "section": {
                    "displayName": team.section.display_name,
                },
                "subTeams": [],
                "teamType": {"displayName": team.team_type.name},
            }
        }

    def test_query__sub_teams(self, user_with_person: User) -> None:
        district = DistrictFactory()
        DistrictUserRole.objects.create(user=user_with_person, district=district, level=DistrictUserRoleType.MANAGER)

        team = GroupSectionTeamFactory()
        sub_teams = TeamFactory.create_batch(size=5, parent_team=team)
        GroupSubTeamFactory()  # Another random sub team

        client = TestClient(self.url)
        with client.login(user_with_person):
            result = client.query(
                self.QUERY,
                variables={"teamId": to_base64("Team", team.id)},  # type: ignore[dict-item]
            )

        assert isinstance(result, Response)

        assert result.errors is None
        assert result.data == {
            "team": {
                "id": to_base64("Team", team.id),
                "displayName": team.display_name,
                "district": None,
                "parentTeam": None,
                "group": None,
                "section": {
                    "displayName": team.section.display_name,
                },
                "subTeams": [
                    {"displayName": st.display_name} for st in sorted(sub_teams, key=lambda st: st.team_type.name)
                ],
                "teamType": {"displayName": team.team_type.name},
            }
        }
