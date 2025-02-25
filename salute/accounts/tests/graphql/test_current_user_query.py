import pytest
from django.urls import reverse
from strawberry_django.test.client import Response, TestClient

from salute.accounts.models import DistrictUserRoleType, User
from salute.hierarchy.factories import DistrictFactory


@pytest.mark.django_db
class TestGetCurrentUserQuery:
    url = reverse("graphql")

    CURRENT_USER_QUERY = """
    query {
        currentUser {
            email
            lastLogin
            userRoles {
                __typename
                ... on UserDistrictRole {
                    level
                }
            }
            person {
                firstName
                displayName
                formattedMembershipNumber
                contactEmail
            }
        }
    }
    """

    def test_current_user_query__not_authenticated(self) -> None:
        client = TestClient(self.url)
        results = client.query(self.CURRENT_USER_QUERY, assert_no_errors=False)

        assert isinstance(results, Response)

        assert results.errors == [
            {"message": "User is not authenticated.", "locations": [{"line": 3, "column": 9}], "path": ["currentUser"]}
        ]
        assert results.data is None

    def test_current_user_query__authenticated(self, user: User) -> None:
        client = TestClient(self.url)
        with client.login(user):
            result = client.query(self.CURRENT_USER_QUERY)

        assert user.last_login
        assert isinstance(result, Response)

        assert result.errors is None
        assert result.data == {
            "currentUser": {
                "email": user.email,
                "lastLogin": user.last_login.isoformat(),
                "userRoles": [],
                "person": None,
            }
        }

    def test_current_user_query__authenticated_with_person(self, user_with_person: User) -> None:
        client = TestClient(self.url)
        with client.login(user_with_person):
            result = client.query(self.CURRENT_USER_QUERY)

        assert user_with_person.last_login
        assert user_with_person.person is not None
        assert isinstance(result, Response)

        assert result.errors is None
        assert result.data == {
            "currentUser": {
                "email": user_with_person.email,
                "lastLogin": user_with_person.last_login.isoformat(),
                "userRoles": [],
                "person": {
                    "firstName": user_with_person.person.first_name,
                    "displayName": user_with_person.person.display_name,
                    "formattedMembershipNumber": user_with_person.person.formatted_membership_number,
                    "contactEmail": user_with_person.person.contact_email,
                },
            }
        }

    @pytest.mark.parametrize("role_type", DistrictUserRoleType)
    def test_current_user_query__authenticated_with_role(self, user: User, role_type: DistrictUserRoleType) -> None:
        district = DistrictFactory()
        user.district_roles.create(district=district, level=role_type)

        client = TestClient(self.url)
        with client.login(user):
            result = client.query(self.CURRENT_USER_QUERY)

        assert isinstance(result, Response)

        assert result.errors is None
        assert result.data["currentUser"]["userRoles"] == [{"__typename": "UserDistrictRole", "level": role_type.name}]  # type: ignore
