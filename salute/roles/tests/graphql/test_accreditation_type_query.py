from uuid import UUID

import pytest
from django.urls import reverse
from strawberry.relay import to_base64
from strawberry_django.test.client import Response, TestClient

from salute.accounts.models import User
from salute.roles.factories import AccreditationTypeFactory


@pytest.mark.django_db
class TestAccreditationTypeQuery:
    url = reverse("graphql")

    QUERY = """
    query getAccreditationType($accreditationTypeId: GlobalID!) {
        accreditationType(accreditationTypeId: $accreditationTypeId) {
            id
            displayName
        }
    }
    """

    def test_query__not_authenticated(self) -> None:
        accreditation_type = AccreditationTypeFactory()
        client = TestClient(self.url)
        results = client.query(
            self.QUERY,
            variables={"accreditationTypeId": to_base64("AccreditationType", accreditation_type.id)},  # type: ignore[dict-item]
            assert_no_errors=False,
        )

        assert isinstance(results, Response)

        assert results.errors == [
            {
                "message": "You don't have permission to view that accreditation type.",
                "locations": [{"line": 3, "column": 9}],
                "path": ["accreditationType"],
            }
        ]
        assert results.data is None

    def test_query__no_permission(self, user: User) -> None:
        accreditation_type = AccreditationTypeFactory()
        client = TestClient(self.url)
        with client.login(user):
            results = client.query(
                self.QUERY,
                variables={"accreditationTypeId": to_base64("AccreditationType", accreditation_type.id)},  # type: ignore[dict-item]
                assert_no_errors=False,
            )

        assert isinstance(results, Response)

        assert results.errors == [
            {
                "message": "You don't have permission to view that accreditation type.",
                "locations": [{"line": 3, "column": 9}],
                "path": ["accreditationType"],
            }
        ]
        assert results.data is None

    def test_query(self, user_with_person: User) -> None:
        accreditation_type = AccreditationTypeFactory()
        client = TestClient(self.url)
        with client.login(user_with_person):
            result = client.query(
                self.QUERY,
                variables={"accreditationTypeId": to_base64("AccreditationType", accreditation_type.id)},  # type: ignore[dict-item]
            )

        assert isinstance(result, Response)

        assert result.errors is None
        assert result.data == {
            "accreditationType": {
                "id": to_base64("AccreditationType", accreditation_type.id),
                "displayName": accreditation_type.name,
            }
        }

    def test_query__not_found(self, user_with_person: User) -> None:
        client = TestClient(self.url)
        with client.login(user_with_person):
            result = client.query(
                self.QUERY,
                variables={"accreditationTypeId": to_base64("AccreditationType", UUID(int=0))},  # type: ignore[dict-item]
                assert_no_errors=False,
            )

        assert isinstance(result, Response)

        assert result.errors == [
            {
                "locations": [{"column": 9, "line": 3}],
                "message": "AccreditationType matching query does not exist.",
                "path": ["accreditationType"],
            }
        ]
        assert result.data is None
