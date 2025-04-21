from typing import Any
from zoneinfo import ZoneInfo

import pytest
from django.urls import reverse
from strawberry.relay import to_base64
from strawberry_django.test.client import Response, TestClient

from salute.accounts.models import DistrictUserRole, DistrictUserRoleType, User
from salute.hierarchy.factories import DistrictFactory
from salute.roles.factories import AccreditationFactory, DistrictTeamFactory
from salute.roles.models import Accreditation


@pytest.mark.django_db
class TestAccreditationListQuery:
    url = reverse("graphql")

    QUERY = """
    query listAccreditations($filters: AccreditationFilter) {
        accreditations(filters: $filters) {
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
                    accreditationType {
                        displayName
                    }
                    status
                    grantedAt
                    expiresAt
                }
            }
        }
    }
    """

    def _get_expected_data_for_accreditation(self, accreditation: Accreditation) -> dict[str, Any]:
        utc = ZoneInfo("UTC")
        return {
            "id": to_base64("Accreditation", accreditation.id),
            "person": {
                "displayName": accreditation.person.display_name,
            },
            "accreditationType": {
                "displayName": accreditation.accreditation_type.name,
            },
            "team": {
                "displayName": accreditation.team.display_name,
                "unit": {
                    "displayName": accreditation.team.unit.display_name,
                },
            },
            "status": accreditation.status,
            "grantedAt": accreditation.granted_at.astimezone(utc).isoformat(),
            "expiresAt": accreditation.expires_at.astimezone(utc).isoformat(),
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
                "message": "You don't have permission to list accreditations.",
                "locations": [{"line": 3, "column": 9}],
                "path": ["accreditations"],
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
                "message": "You don't have permission to list accreditations.",
                "locations": [{"line": 3, "column": 9}],
                "path": ["accreditations"],
            }
        ]
        assert results.data is None

    def test_query__no_permission(self, user_with_person: User) -> None:
        AccreditationFactory(team=DistrictTeamFactory())

        client = TestClient(self.url)
        with client.login(user_with_person):
            results = client.query(
                self.QUERY,
                assert_no_errors=False,
            )

        assert isinstance(results, Response)

        assert results.data == {"accreditations": {"totalCount": 0, "edges": []}}
        assert results.errors is None

    def test_query__just_own_accreditations(self, user_with_person: User) -> None:
        AccreditationFactory(team=DistrictTeamFactory())
        accreditation = AccreditationFactory(team=DistrictTeamFactory(), person=user_with_person.person)

        client = TestClient(self.url)
        with client.login(user_with_person):
            results = client.query(
                self.QUERY,
                assert_no_errors=False,
            )

        assert isinstance(results, Response)

        assert results.data == {
            "accreditations": {
                "totalCount": 1,
                "edges": [{"node": self._get_expected_data_for_accreditation(accreditation)}],
            }
        }
        assert results.errors is None

    def test_query(self, user_with_person: User) -> None:
        district = DistrictFactory()
        DistrictUserRole.objects.create(user=user_with_person, district=district, level=DistrictUserRoleType.MANAGER)

        accreditations = AccreditationFactory.create_batch(size=10, team__district=district)
        client = TestClient(self.url)
        with client.login(user_with_person):
            result = client.query(
                self.QUERY,
            )

        assert isinstance(result, Response)

        assert result.errors is None
        assert result.data == {
            "accreditations": {
                "edges": [
                    {"node": self._get_expected_data_for_accreditation(accreditation)}
                    for accreditation in sorted(
                        accreditations, key=lambda accreditation: accreditation.team.display_name
                    )
                ],
                "totalCount": 10,
            }
        }

    def test_query__filter__by_person(self, user_with_person: User) -> None:
        assert user_with_person.person

        district = DistrictFactory()
        DistrictUserRole.objects.create(user=user_with_person, district=district, level=DistrictUserRoleType.MANAGER)

        expected_accreditation = AccreditationFactory(person=user_with_person.person, team__district=district)
        AccreditationFactory.create_batch(size=10, team__district=district)

        client = TestClient(self.url)
        with client.login(user_with_person):
            result = client.query(
                self.QUERY,
                variables={
                    "filters": {
                        "person": {"id": {"exact": to_base64("Person", user_with_person.person.id)}},
                    },
                },
            )

        assert isinstance(result, Response)

        assert result.errors is None
        assert result.data == {
            "accreditations": {
                "edges": [{"node": self._get_expected_data_for_accreditation(expected_accreditation)}],
                "totalCount": 1,
            }
        }

    def test_query__filter__by_team(self, user_with_person: User) -> None:
        assert user_with_person.person

        district = DistrictFactory()
        DistrictUserRole.objects.create(user=user_with_person, district=district, level=DistrictUserRoleType.MANAGER)

        team = DistrictTeamFactory(district=district)
        expected_accreditation = AccreditationFactory(person=user_with_person.person, team=team)
        AccreditationFactory.create_batch(size=10, team__district=district)

        client = TestClient(self.url)
        with client.login(user_with_person):
            result = client.query(
                self.QUERY,
                variables={
                    "filters": {
                        "team": {"id": {"exact": to_base64("Team", team.id)}},
                    },
                },
            )

        assert isinstance(result, Response)

        assert result.errors is None
        assert result.data == {
            "accreditations": {
                "edges": [{"node": self._get_expected_data_for_accreditation(expected_accreditation)}],
                "totalCount": 1,
            }
        }
