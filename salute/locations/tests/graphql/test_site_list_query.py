import pytest
from django.urls import reverse
from strawberry.relay import to_base64
from strawberry_django.test.client import Response, TestClient

from salute.accounts.models import User
from salute.locations.factories import SiteFactory


@pytest.mark.django_db
class TestSiteListQuery:
    url = reverse("graphql")

    QUERY = """
    query listSites($filters: SiteFilter) {
        sites(filters: $filters) {
            totalCount
            edges {
                node {
                    id
                    displayName
                }
            }
            centroid {
                latitude
                longitude
            }
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
                "message": "You don't have permission to list sites.",
                "locations": [{"line": 3, "column": 9}],
                "path": ["sites"],
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
                "message": "You don't have permission to list sites.",
                "locations": [{"line": 3, "column": 9}],
                "path": ["sites"],
            }
        ]
        assert results.data is None

    def test_query__none(self, user_with_person: User) -> None:
        client = TestClient(self.url)
        with client.login(user_with_person):
            result = client.query(
                self.QUERY,
            )

        assert isinstance(result, Response)

        assert result.errors is None
        assert result.data == {
            "sites": {
                "edges": [],
                "totalCount": 0,
                "centroid": None,
            }
        }

    def test_query(self, user_with_person: User) -> None:
        sites = SiteFactory.create_batch(size=10, longitude=1, latitude=1)
        client = TestClient(self.url)
        with client.login(user_with_person):
            result = client.query(
                self.QUERY,
            )

        assert isinstance(result, Response)

        assert result.errors is None
        assert result.data == {
            "sites": {
                "edges": [
                    {
                        "node": {
                            "id": to_base64("Site", site.id),
                            "displayName": site.name,
                        }
                    }
                    for site in sorted(sites, key=lambda site: site.name)
                ],
                "totalCount": 10,
                "centroid": {
                    "latitude": 1,
                    "longitude": 1,
                },
            }
        }
