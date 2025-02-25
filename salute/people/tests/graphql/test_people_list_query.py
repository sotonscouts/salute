import pytest
from django.urls import reverse
from strawberry_django.test.client import Response, TestClient

from salute.accounts.models import DistrictUserRole, DistrictUserRoleType, User
from salute.hierarchy.factories import DistrictFactory
from salute.people.factories import PersonFactory
from salute.people.models import Person


@pytest.mark.django_db
class TestPersonListQuery:
    url = reverse("graphql")

    QUERY = """
    query {
        people {
            edges {
                node {
                    displayName
                    firstName
                    formattedMembershipNumber
                    contactEmail
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
                "message": "You don't have permission to list people.",
                "locations": [{"line": 3, "column": 9}],
                "path": ["people"],
            }
        ]
        assert results.data is None

    def test_query__no_person_associated_to_user(self, user: User) -> None:
        client = TestClient(self.url)
        with client.login(user):
            results = client.query(
                self.QUERY,
                assert_no_errors=False,
            )

        assert isinstance(results, Response)

        assert results.errors == [
            {
                "message": "You don't have permission to list people.",
                "locations": [{"line": 3, "column": 9}],
                "path": ["people"],
            }
        ]
        assert results.data is None

    def test_query__just_current_person(self, user_with_person: User) -> None:
        PersonFactory.create_batch(5)
        client = TestClient(self.url)
        with client.login(user_with_person):
            results = client.query(
                self.QUERY,
                assert_no_errors=False,
            )

        assert isinstance(results, Response)
        assert user_with_person.person is not None

        assert results.errors is None
        assert results.data == {
            "people": {
                "edges": [
                    {
                        "node": {
                            "displayName": user_with_person.person.display_name,
                            "firstName": user_with_person.person.first_name,
                            "formattedMembershipNumber": user_with_person.person.formatted_membership_number,
                            "contactEmail": user_with_person.person.contact_email,
                        }
                    }
                ],
                "totalCount": 1,
            }
        }

    def test_query__district_admin(self, user_with_person: User) -> None:
        district = DistrictFactory()
        DistrictUserRole.objects.create(user=user_with_person, district=district, level=DistrictUserRoleType.ADMIN)

        PersonFactory.create_batch(5)
        client = TestClient(self.url)
        with client.login(user_with_person):
            results = client.query(
                self.QUERY,
                assert_no_errors=False,
            )

        assert isinstance(results, Response)

        assert results.errors is None
        assert results.data == {
            "people": {
                "edges": [
                    {
                        "node": {
                            "displayName": person.display_name,
                            "firstName": person.first_name,
                            "formattedMembershipNumber": person.formatted_membership_number,
                            "contactEmail": person.contact_email,
                        }
                    }
                    for person in Person.objects.order_by("display_name")
                ],
                "totalCount": 6,
            }
        }

    def test_query__district_manager(self, user_with_person: User) -> None:
        district = DistrictFactory()
        DistrictUserRole.objects.create(user=user_with_person, district=district, level=DistrictUserRoleType.MANAGER)

        PersonFactory.create_batch(5)
        client = TestClient(self.url)
        with client.login(user_with_person):
            results = client.query(
                self.QUERY,
                assert_no_errors=False,
            )

        assert isinstance(results, Response)

        assert results.errors is None
        assert results.data == {
            "people": {
                "edges": [
                    {
                        "node": {
                            "displayName": person.display_name,
                            "firstName": person.first_name,
                            "formattedMembershipNumber": person.formatted_membership_number,
                            # We are permitted to see the email address of the person if they are the current user
                            "contactEmail": person.contact_email if person == user_with_person.person else None,
                        }
                    }
                    for person in Person.objects.order_by("display_name")
                ],
                "totalCount": 6,
            }
        }

    @pytest.mark.parametrize(
        ("field", "ordering", "reverse"),
        [
            pytest.param("display_name", "ASC", False, id="display_name-asc"),
            pytest.param("display_name", "DESC", True, id="display_name-desc"),
            pytest.param("first_name", "ASC", False, id="first_name-asc"),
            pytest.param("first_name", "DESC", True, id="first_name-desc"),
        ],
    )
    def test_query__ordering(self, *, field: str, ordering: str, reverse: bool, user_with_person: User) -> None:
        district = DistrictFactory()
        DistrictUserRole.objects.create(user=user_with_person, district=district, level=DistrictUserRoleType.MANAGER)

        PersonFactory.create_batch(10)

        field_title_case = field.title().replace("_", "")
        field_camel_case = field_title_case[0].lower() + field_title_case[1:]

        client = TestClient(self.url)
        with client.login(user_with_person):
            result = client.query(
                """
                query personOrderTest($order: Ordering) {
                    people (order: {firstName: $order}) {
                        edges {
                            node {
                """
                f"                {field_camel_case}"
                """
                            }
                        }
                    }
                }
                """,
                variables={"order": ordering},  # type: ignore[dict-item]
            )

        assert isinstance(result, Response)

        assert result.errors is None
        assert result.data == {
            "people": {
                "edges": [
                    {
                        "node": {
                            field_camel_case: getattr(p, field),
                        }
                    }
                    for p in Person.objects.order_by(field if not reverse else f"-{field}")
                ],
            }
        }
