import pytest
from django.urls import reverse
from strawberry.relay import to_base64
from strawberry_django.test.client import Response, TestClient

from salute.accounts.models import DistrictUserRole, DistrictUserRoleType, User
from salute.hierarchy.factories import DistrictFactory
from salute.people.factories import PersonFactory
from salute.people.models import Person


@pytest.mark.django_db
class TestPersonListQuery:
    url = reverse("graphql")

    QUERY = """
    query listPeople($filters: PersonFilter, $order: PersonOrder!) {
        people(filters: $filters, ordering: [$order]) {
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
            variables={"order": {"displayName": "ASC"}},
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
                variables={"order": {"displayName": "ASC"}},
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
                variables={"order": {"displayName": "ASC"}},
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
                variables={"order": {"displayName": "ASC"}},
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
                variables={"order": {"displayName": "ASC"}},
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
        DistrictUserRole.objects.create(user=user_with_person, district=district, level=DistrictUserRoleType.ADMIN)

        PersonFactory.create_batch(10)

        field_title_case = field.title().replace("_", "")
        field_camel_case = field_title_case[0].lower() + field_title_case[1:]

        client = TestClient(self.url)
        with client.login(user_with_person):
            result = client.query(
                self.QUERY,
                variables={"order": {field_camel_case: ordering}},
            )

        assert isinstance(result, Response)

        assert result.errors is None
        assert result.data == {
            "people": {
                "edges": [
                    {
                        "node": {
                            "displayName": p.display_name,
                            "firstName": p.first_name,
                            "formattedMembershipNumber": p.formatted_membership_number,
                            "contactEmail": p.contact_email,
                        }
                    }
                    for p in Person.objects.order_by(field if not reverse else f"-{field}")
                ],
                "totalCount": 11,
            }
        }

    def test_query__filter__id(self, user_with_person: User) -> None:
        district = DistrictFactory()
        DistrictUserRole.objects.create(user=user_with_person, district=district, level=DistrictUserRoleType.ADMIN)

        people = [
            PersonFactory(legal_name="A", preferred_name="", last_name="A"),
            PersonFactory(legal_name="B", preferred_name="", last_name="B"),
            PersonFactory(legal_name="D", preferred_name="C", last_name="C"),
        ]
        expected_people = people[0:2]
        assert len(expected_people) == 2

        client = TestClient(self.url)
        with client.login(user_with_person):
            result = client.query(
                self.QUERY,
                variables={
                    "order": {"displayName": "ASC"},
                    "filters": {
                        "id": {
                            "inList": [to_base64("Person", person.id) for person in expected_people],
                        }
                    },
                },
            )

        assert isinstance(result, Response)

        assert result.errors is None
        assert result.data == {
            "people": {
                "edges": [
                    {
                        "node": {
                            "displayName": p.display_name,
                            "firstName": p.first_name,
                            "formattedMembershipNumber": p.formatted_membership_number,
                            "contactEmail": p.contact_email,
                        }
                    }
                    for p in sorted(expected_people, key=lambda p: p.display_name)
                ],
                "totalCount": 2,
            }
        }

    def test_query__filter__display_name(self, user_with_person: User) -> None:
        district = DistrictFactory()
        DistrictUserRole.objects.create(user=user_with_person, district=district, level=DistrictUserRoleType.ADMIN)

        people = [
            PersonFactory(legal_name="Aaaa", preferred_name="", last_name="Aaaaaason"),
            PersonFactory(legal_name="B", preferred_name="", last_name="B"),
            PersonFactory(legal_name="D", preferred_name="C", last_name="C"),
        ]
        expected_person = people[0]

        client = TestClient(self.url)
        with client.login(user_with_person):
            result = client.query(
                self.QUERY,
                variables={"filters": {"displayName": {"exact": "Aaaa Aaaaaason"}}, "order": {"displayName": "ASC"}},
            )

        assert isinstance(result, Response)

        assert result.errors is None
        assert result.data == {
            "people": {
                "edges": [
                    {
                        "node": {
                            "displayName": expected_person.display_name,
                            "firstName": expected_person.first_name,
                            "formattedMembershipNumber": expected_person.formatted_membership_number,
                            "contactEmail": expected_person.contact_email,
                        }
                    }
                ],
                "totalCount": 1,
            }
        }
