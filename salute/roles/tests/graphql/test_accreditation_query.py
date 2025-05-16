from typing import Any
from zoneinfo import ZoneInfo

import pytest
from django.urls import reverse
from strawberry.relay import to_base64
from strawberry_django.test.client import Response, TestClient

from salute.accounts.models import DistrictUserRole, DistrictUserRoleType, User
from salute.hierarchy.factories import DistrictFactory
from salute.people.factories import PersonFactory
from salute.roles.factories import AccreditationFactory
from salute.roles.models import Accreditation


@pytest.mark.django_db
class TestAccreditationQuery:
    url = reverse("graphql")

    QUERY = """
    query getAccreditation($id: ID!) {
        accreditation(accreditationId: $id) {
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
            variables={"id": "UGVyc29uTm9kZTox"},  # type: ignore[dict-item]
            assert_no_errors=False,
        )

        assert isinstance(results, Response)

        assert results.errors == [
            {
                "message": "You don't have permission to view that accreditation.",
                "locations": [{"line": 3, "column": 9}],
                "path": ["accreditation"],
            }
        ]
        assert results.data is None

    def test_query__no_person_associated_to_user(self, user: User) -> None:
        accreditation = AccreditationFactory(team__district=DistrictFactory())
        client = TestClient(self.url)
        with client.login(user):
            results = client.query(
                self.QUERY,
                variables={"id": to_base64("Accreditation", accreditation.id)},  # type: ignore[dict-item]
                assert_no_errors=False,
            )

        assert isinstance(results, Response)

        assert results.errors == [
            {
                "message": "You don't have permission to view that accreditation.",
                "locations": [{"line": 3, "column": 9}],
                "path": ["accreditation"],
            }
        ]
        assert results.data is None

    def test_query__own_accreditation(self, user_with_person: User) -> None:
        accreditation = AccreditationFactory(person=user_with_person.person, team__district=DistrictFactory())
        client = TestClient(self.url)
        with client.login(user_with_person):
            results = client.query(
                self.QUERY,
                variables={"id": to_base64("Accreditation", accreditation.id)},  # type: ignore[dict-item]
            )

        assert isinstance(results, Response)

        assert results.errors is None
        assert results.data == {
            "accreditation": self._get_expected_data_for_accreditation(accreditation),
        }

    def test_query__cannot_query_other_accreditation(self, user_with_person: User) -> None:
        person = PersonFactory()
        accreditation = AccreditationFactory(person=person, team__district=DistrictFactory())
        client = TestClient(self.url)
        with client.login(user_with_person):
            results = client.query(
                self.QUERY,
                variables={"id": to_base64("Accreditation", accreditation.id)},  # type: ignore[dict-item]
                assert_no_errors=False,
            )

        assert isinstance(results, Response)

        assert results.errors == [
            {
                "message": "You don't have permission to view that accreditation.",
                "locations": [{"line": 3, "column": 9}],
                "path": ["accreditation"],
            }
        ]
        assert results.data is None

    @pytest.mark.parametrize("role", DistrictUserRoleType)
    def test_query__role_can_query_other_accreditation(
        self, role: DistrictUserRoleType, user_with_person: User
    ) -> None:
        district = DistrictFactory()
        DistrictUserRole.objects.create(user=user_with_person, district=district, level=role)
        person = PersonFactory()
        accreditation = AccreditationFactory(person=person, team__district=district)
        client = TestClient(self.url)
        with client.login(user_with_person):
            results = client.query(
                self.QUERY,
                variables={"id": to_base64("Accreditation", accreditation.id)},  # type: ignore[dict-item]
            )

        assert isinstance(results, Response)

        assert results.errors is None
        assert results.data == {
            "accreditation": self._get_expected_data_for_accreditation(accreditation),
        }
