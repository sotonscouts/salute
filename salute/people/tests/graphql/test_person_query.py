from collections.abc import Generator

import pytest
import pytest_django
from django.urls import reverse
from strawberry.relay import to_base64
from strawberry_django.test.client import Response, TestClient

from salute.accounts.models import DistrictUserRole, DistrictUserRoleType, User
from salute.hierarchy.factories import DistrictFactory
from salute.integrations.workspace.factories import WorkspaceAccountFactory
from salute.people.factories import PersonFactory
from salute.people.utils import format_phone_number
from salute.roles.factories import AccreditationFactory, RoleFactory


@pytest.mark.django_db
class TestPersonQuery:
    url = reverse("graphql")

    QUERY = """
    query getPerson($id: ID!) {
        person(personId: $id) {
            displayName
            firstName
            formattedMembershipNumber
            contactEmail
            phoneNumber
            alternatePhoneNumber
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
                # User can see their own phone numbers
                "phoneNumber": format_phone_number(user_with_person.person.phone_number),
                "alternatePhoneNumber": format_phone_number(user_with_person.person.alternate_phone_number),
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
                # District Admin can see phone numbers
                "phoneNumber": format_phone_number(person.phone_number),
                "alternatePhoneNumber": format_phone_number(person.alternate_phone_number),
            }
        }

    def test_query__district_manager__no_workspace_account(self, user_with_person: User) -> None:
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
                "contactEmail": None,  # no workspace account, so no contact email
                # District Manager cannot see other's phone numbers
                "phoneNumber": None,
                "alternatePhoneNumber": None,
            }
        }

    def test_query__district_manager__with_workspace_account(self, user_with_person: User) -> None:
        district = DistrictFactory()
        DistrictUserRole.objects.create(user=user_with_person, district=district, level=DistrictUserRoleType.MANAGER)

        person = PersonFactory()
        workspace_account = WorkspaceAccountFactory(person=person)
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
                "contactEmail": workspace_account.primary_email,  # workspace email
                # District Manager cannot see other's phone numbers
                "phoneNumber": None,
                "alternatePhoneNumber": None,
            }
        }


@pytest.mark.django_db
class TestPersonTSAProfileLinkQuery:
    url = reverse("graphql")

    QUERY = """
    query getPerson($id: ID!) {
        person(personId: $id) {
            tsaProfileLink
        }
    }
    """

    @pytest.fixture(autouse=True)
    def use_dummy_tsa_person_profile_link_template(
        self, settings: Generator[pytest_django.fixtures.SettingsWrapper, None, None]
    ) -> None:
        settings.TSA_PERSON_PROFILE_LINK_TEMPLATE = "https://example.com/people/$tsaid/"  # type: ignore[attr-defined]

    def test_query_tsa_profile_link(self, user_with_person: User) -> None:
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
                "tsaProfileLink": f"https://example.com/people/{user_with_person.person.tsa_id}/",
            }
        }


@pytest.mark.django_db
class TestPersonJoinRolesQuery:
    url = reverse("graphql")

    QUERY = """
    query getPerson($id: ID!) {
        person(personId: $id) {
            displayName
            roles {
                edges {
                    node {
                        team {
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

    def test_query__no_roles(self, user_with_person: User) -> None:
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
                "roles": {
                    "edges": [],
                    "totalCount": 0,
                },
            }
        }

    def test_query(self, user_with_person: User) -> None:
        assert user_with_person.person is not None
        roles = RoleFactory.create_batch(size=5, person=user_with_person.person)
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
                "roles": {
                    "edges": [
                        {
                            "node": {
                                "team": {"displayName": role.team.display_name},
                                "roleType": {"displayName": role.role_type.name},
                                "status": {"displayName": role.status.name},
                            }
                        }
                        for role in sorted(roles, key=lambda r: (r.team.team_type.name))
                    ],
                    "totalCount": 5,
                },
            }
        }


@pytest.mark.django_db
class TestPersonJoinAccreditationsQuery:
    url = reverse("graphql")

    QUERY = """
    query getPerson($id: ID!) {
        person(personId: $id) {
            displayName
            accreditations {
                edges {
                    node {
                        team {
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

    def test_query__no_accreditations(self, user_with_person: User) -> None:
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
                "accreditations": {
                    "edges": [],
                    "totalCount": 0,
                },
            }
        }

    def test_query(self, user_with_person: User) -> None:
        assert user_with_person.person is not None
        accreditations = AccreditationFactory.create_batch(size=5, person=user_with_person.person)
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
                "accreditations": {
                    "edges": [
                        {
                            "node": {
                                "team": {"displayName": accreditation.team.display_name},
                                "accreditationType": {"displayName": accreditation.accreditation_type.name},
                                "status": accreditation.status,
                            }
                        }
                        for accreditation in sorted(accreditations, key=lambda r: (r.team.team_type.name))
                    ],
                    "totalCount": 5,
                },
            }
        }


@pytest.mark.django_db
class TestPersonJoinWorkspaceAccountQuery:
    url = reverse("graphql")

    QUERY = """
    query getPerson($id: ID!) {
        person(personId: $id) {
            displayName
            workspaceAccount {
                id
            }
        }
    }
    """

    def test_query__no_workspace_account(self, user_with_person: User) -> None:
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
            "person": {"displayName": user_with_person.person.display_name, "workspaceAccount": None}
        }

    def test_query(self, user_with_person: User) -> None:
        assert user_with_person.person is not None
        workspace_account = WorkspaceAccountFactory(person=user_with_person.person)
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
                "workspaceAccount": {"id": to_base64("WorkspaceAccount", workspace_account.id)},
            }
        }
