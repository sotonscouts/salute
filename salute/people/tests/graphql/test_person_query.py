import pytest
from django.urls import reverse
from strawberry.relay import to_base64
from strawberry_django.test.client import Response, TestClient

from salute.accounts.models import DistrictUserRole, DistrictUserRoleType, User
from salute.hierarchy.factories import DistrictFactory
from salute.people.factories import PersonFactory


@pytest.mark.django_db
class TestPersonQuery:
    url = reverse("graphql")

    QUERY = """
    query getPerson($id: GlobalID!) {
        person(personId: $id) {
            displayName
            firstName
            formattedMembershipNumber
            contactEmail
        }
    }
    """

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
                "message": "You don't have permission to view that person.",
                "locations": [{"line": 3, "column": 9}],
                "path": ["person"],
            }
        ]
        assert results.data is None

    def test_query__no_person_associated_to_user(self, user: User) -> None:
        person = PersonFactory()
        client = TestClient(self.url)
        with client.login(user):
            results = client.query(
                self.QUERY,
                variables={"id": to_base64("Person", person.id)},  # type: ignore[dict-item]
                assert_no_errors=False,
            )

        assert isinstance(results, Response)

        assert results.errors == [
            {
                "message": "You don't have permission to view that person.",
                "locations": [{"line": 3, "column": 9}],
                "path": ["person"],
            }
        ]
        assert results.data is None

    def test_query__current_person(self, user_with_person: User) -> None:
        assert user_with_person.person is not None
        client = TestClient(self.url)
        with client.login(user_with_person):
            results = client.query(
                self.QUERY,
                variables={"id": to_base64("Person", user_with_person.person.id)},  # type: ignore[dict-item]
            )

        assert isinstance(results, Response)

        assert results.errors is None
        assert results.data == {
            "person": {
                "displayName": user_with_person.person.display_name,
                "firstName": user_with_person.person.first_name,
                "formattedMembershipNumber": user_with_person.person.formatted_membership_number,
                "contactEmail": user_with_person.person.contact_email,
            }
        }

    def test_query__other_person(self, user_with_person: User) -> None:
        person = PersonFactory()
        client = TestClient(self.url)
        with client.login(user_with_person):
            results = client.query(
                self.QUERY,
                variables={"id": to_base64("Person", person.id)},  # type: ignore[dict-item]
                assert_no_errors=False,
            )

        assert isinstance(results, Response)

        assert results.errors == [
            {
                "message": "You don't have permission to view that person.",
                "locations": [{"line": 3, "column": 9}],
                "path": ["person"],
            }
        ]
        assert results.data is None

    def test_query__district_admin(self, user_with_person: User) -> None:
        district = DistrictFactory()
        DistrictUserRole.objects.create(user=user_with_person, district=district, level=DistrictUserRoleType.ADMIN)

        person = PersonFactory()
        client = TestClient(self.url)
        with client.login(user_with_person):
            results = client.query(
                self.QUERY,
                variables={"id": to_base64("Person", person.id)},  # type: ignore[dict-item]
                assert_no_errors=False,
            )

        assert isinstance(results, Response)

        assert results.errors is None
        assert results.data == {
            "person": {
                "displayName": person.display_name,
                "firstName": person.first_name,
                "formattedMembershipNumber": person.formatted_membership_number,
                "contactEmail": person.contact_email,
            }
        }

    def test_query__district_manager(self, user_with_person: User) -> None:
        district = DistrictFactory()
        DistrictUserRole.objects.create(user=user_with_person, district=district, level=DistrictUserRoleType.MANAGER)

        person = PersonFactory()
        client = TestClient(self.url)
        with client.login(user_with_person):
            results = client.query(
                self.QUERY,
                variables={"id": to_base64("Person", person.id)},  # type: ignore[dict-item]
                assert_no_errors=False,
            )

        assert isinstance(results, Response)

        assert results.errors is None
        assert results.data == {
            "person": {
                "displayName": person.display_name,
                "firstName": person.first_name,
                "formattedMembershipNumber": person.formatted_membership_number,
                "contactEmail": None,
            }
        }
