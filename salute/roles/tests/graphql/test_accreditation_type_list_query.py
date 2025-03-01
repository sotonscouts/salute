import pytest
from django.urls import reverse
from strawberry.relay import to_base64
from strawberry_django.test.client import Response, TestClient

from salute.accounts.models import User
from salute.roles.factories import AccreditationTypeFactory


@pytest.mark.django_db
class TestAccreditationTypeListQuery:
    url = reverse("graphql")

    QUERY = """
    query {
        accreditationTypes {
            edges {
                node {
                    id
                    displayName
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
                "message": "You don't have permission to list accreditation types.",
                "locations": [{"line": 3, "column": 9}],
                "path": ["accreditationTypes"],
            }
        ]
        assert results.data is None

    def test_query__no_permission(self, user: User) -> None:
        client = TestClient(self.url)
        with client.login(user):
            results = client.query(
                self.QUERY,
                assert_no_errors=False,
            )

        assert isinstance(results, Response)

        assert results.errors == [
            {
                "message": "You don't have permission to list accreditation types.",
                "locations": [{"line": 3, "column": 9}],
                "path": ["accreditationTypes"],
            }
        ]
        assert results.data is None

    def test_query(self, user_with_person: User) -> None:
        accreditation_types = AccreditationTypeFactory.create_batch(size=5)
        client = TestClient(self.url)
        with client.login(user_with_person):
            result = client.query(
                self.QUERY,
            )

        assert isinstance(result, Response)

        assert result.errors is None
        assert result.data == {
            "accreditationTypes": {
                "edges": [
                    {
                        "node": {
                            "id": to_base64("AccreditationType", at.id),
                            "displayName": at.name,
                        }
                    }
                    for at in sorted(accreditation_types, key=lambda at: at.name)
                ],
                "totalCount": 5,
            }
        }
