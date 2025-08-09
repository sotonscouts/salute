from collections.abc import Generator
from uuid import UUID

import pytest
import pytest_django
from django.urls import reverse
from strawberry.relay import to_base64
from strawberry_django.test.client import Response, TestClient

from salute.accounts.models import DistrictUserRole, DistrictUserRoleType, User
from salute.hierarchy.factories import DistrictFactory
from salute.roles.factories import (
    AccreditationFactory,
    DistrictTeamFactory,
    GroupSectionTeamFactory,
    GroupSubTeamFactory,
    GroupTeamFactory,
    RoleFactory,
    TeamFactory,
)


@pytest.mark.django_db
class TestTeamQuery:
    url = reverse("graphql")

    QUERY = """
    query getTeam($teamId: ID!) {
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


@pytest.mark.django_db
class TestTeamPersonCountQuery:
    url = reverse("graphql")
    QUERY = """
    query getTeam($teamId: ID!) {
        team(teamId: $teamId) {
            personCount
        }
    }
    """

    def test_query__person_count__no_role(self, user_with_person: User) -> None:
        team = DistrictTeamFactory()
        client = TestClient(self.url)
        with client.login(user_with_person):
            result = client.query(
                self.QUERY,
                variables={"teamId": to_base64("Team", team.id)},  # type: ignore[dict-item]
            )

        assert isinstance(result, Response)

        assert result.errors is None
        assert result.data == {
            "team": {"personCount": None},
        }

    def test_query__person_count(self, user_with_person: User) -> None:
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
            "team": {"personCount": 0},
        }

    def test_query__person_count_with_roles(self, user_with_person: User) -> None:
        district = DistrictFactory()
        DistrictUserRole.objects.create(user=user_with_person, district=district, level=DistrictUserRoleType.ADMIN)

        team = DistrictTeamFactory(district=district)
        roles = RoleFactory.create_batch(size=5, team=team)
        RoleFactory(team=team, person=roles[0].person)  # Add a duplicate role
        client = TestClient(self.url)
        with client.login(user_with_person):
            result = client.query(
                self.QUERY,
                variables={"teamId": to_base64("Team", team.id)},  # type: ignore[dict-item]
            )

        assert isinstance(result, Response)

        assert result.errors is None
        assert result.data == {
            "team": {"personCount": 5},
        }


@pytest.mark.django_db
class TestTeamTSAProfileLinkQuery:
    url = reverse("graphql")

    QUERY = """
    query getTeam($teamId: ID!) {
        team(teamId: $teamId) {
            tsaDetailsLink
        }
    }
    """

    @pytest.fixture(autouse=True)
    def use_dummy_tsa_team_link_template(
        self, settings: Generator[pytest_django.fixtures.SettingsWrapper, None, None]
    ) -> None:
        settings.TSA_TEAM_LINK_TEMPLATE = "https://example.com/units/$unitid/teams/$teamtypeid/"  # type: ignore[attr-defined]

    def test_query_tsa_details_link(self, user_with_person: User) -> None:
        team = GroupTeamFactory()
        client = TestClient(self.url)
        with client.login(user_with_person):
            results = client.query(
                self.QUERY,
                variables={"teamId": to_base64("Team", team.id)},  # type: ignore[dict-item]
            )

        assert isinstance(results, Response)

        assert results.errors is None
        assert results.data == {
            "team": {
                "tsaDetailsLink": f"https://example.com/units/{team.group.tsa_id}/teams/{team.team_type.tsa_id}/",
            }
        }


@pytest.mark.django_db
class TestTeamJoinRolesQuery:
    url = reverse("graphql")

    QUERY = """
    query getTeamWithRoles($teamId: ID!) {
        team(teamId: $teamId) {
            id
            displayName
            roles {
                edges {
                    node {
                        person {
                            displayName
                        }
                        roleType {
                            displayName
                        }
                        status {
                            displayName
                        }
                    }
                }
                totalCount
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

    def test_query__no_roles(self, user_with_person: User) -> None:
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
                "roles": {
                    "edges": [],
                    "totalCount": 0,
                },
            }
        }

    def test_query__roles(self, user_with_person: User) -> None:
        district = DistrictFactory()
        DistrictUserRole.objects.create(user=user_with_person, district=district, level=DistrictUserRoleType.MANAGER)

        team = DistrictTeamFactory(district=district)

        roles = RoleFactory.create_batch(size=5, team=team)

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
                "roles": {
                    "edges": [
                        {
                            "node": {
                                "person": {"displayName": role.person.display_name},
                                "roleType": {"displayName": role.role_type.name},
                                "status": {"displayName": role.status.name},
                            }
                        }
                        for role in sorted(roles, key=lambda r: (r.role_type.name, r.person.display_name))
                    ],
                    "totalCount": 5,
                },
            }
        }

    def test_query__only_own_roles(self, user_with_person: User) -> None:
        district = DistrictFactory()
        team = DistrictTeamFactory(district=district)

        RoleFactory.create_batch(size=5, team=team)
        role = RoleFactory(team=team, person=user_with_person.person)

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
                "roles": {
                    "edges": [
                        {
                            "node": {
                                "person": {"displayName": role.person.display_name},
                                "roleType": {"displayName": role.role_type.name},
                                "status": {"displayName": role.status.name},
                            }
                        }
                    ],
                    "totalCount": 1,
                },
            }
        }


@pytest.mark.django_db
class TestTeamJoinAccreditationsQuery:
    url = reverse("graphql")

    QUERY = """
    query getTeamWithAccreditations($teamId: ID!) {
        team(teamId: $teamId) {
            id
            displayName
            accreditations {
                edges {
                    node {
                        person {
                            displayName
                        }
                        accreditationType {
                            displayName
                        }
                        status
                    }
                }
                totalCount
            }
        }
    }
    """

    def test_query__not_authenticated(self) -> None:
        team = DistrictTeamFactory()
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
        team = DistrictTeamFactory()
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

    def test_query__no_accreditations(self, user_with_person: User) -> None:
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
                "accreditations": {
                    "edges": [],
                    "totalCount": 0,
                },
            }
        }

    def test_query__roles(self, user_with_person: User) -> None:
        district = DistrictFactory()
        DistrictUserRole.objects.create(user=user_with_person, district=district, level=DistrictUserRoleType.MANAGER)

        team = DistrictTeamFactory(district=district)

        accreditations = AccreditationFactory.create_batch(size=5, team=team)

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
                "accreditations": {
                    "edges": [
                        {
                            "node": {
                                "person": {"displayName": accreditation.person.display_name},
                                "accreditationType": {"displayName": accreditation.accreditation_type.name},
                                "status": accreditation.status,
                            }
                        }
                        for accreditation in sorted(
                            accreditations, key=lambda r: (r.accreditation_type.name, r.person.display_name)
                        )
                    ],
                    "totalCount": 5,
                },
            }
        }

    def test_query__only_own_accreditations(self, user_with_person: User) -> None:
        district = DistrictFactory()
        team = DistrictTeamFactory(district=district)

        AccreditationFactory.create_batch(size=5, team=team)
        accreditation = AccreditationFactory(team=team, person=user_with_person.person)

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
                "accreditations": {
                    "edges": [
                        {
                            "node": {
                                "person": {"displayName": accreditation.person.display_name},
                                "accreditationType": {"displayName": accreditation.accreditation_type.name},
                                "status": accreditation.status,
                            }
                        }
                    ],
                    "totalCount": 1,
                },
            }
        }
