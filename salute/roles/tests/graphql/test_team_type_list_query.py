import pytest
from django.urls import reverse
from strawberry.relay import to_base64
from strawberry_django.test.client import Response, TestClient

from salute.accounts.models import User
from salute.roles.factories import TeamTypeFactory


@pytest.mark.django_db
class TestTeamTypeListQuery:
    url = reverse("graphql")

    QUERY = """
    query listTeamTypes($filters: TeamTypeFilter) {
        teamTypes(filters: $filters) {
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
                "message": "You don't have permission to list team types.",
                "locations": [{"line": 3, "column": 9}],
                "path": ["teamTypes"],
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
                "message": "You don't have permission to list team types.",
                "locations": [{"line": 3, "column": 9}],
                "path": ["teamTypes"],
            }
        ]
        assert results.data is None

    def test_query(self, user_with_person: User) -> None:
        team_types = TeamTypeFactory.create_batch(size=5)
        client = TestClient(self.url)
        with client.login(user_with_person):
            result = client.query(
                self.QUERY,
            )

        assert isinstance(result, Response)

        assert result.errors is None
        assert result.data == {
            "teamTypes": {
                "edges": [
                    {
                        "node": {
                            "id": to_base64("TeamType", tt.id),
                            "displayName": tt.name,
                        }
                    }
                    for tt in sorted(team_types, key=lambda tt: tt.name)
                ],
                "totalCount": 5,
            }
        }

    def test_query__filter_by_id(self, user_with_person: User) -> None:
        team_types = TeamTypeFactory.create_batch(size=5)
        expected_team_type = team_types[0]
        client = TestClient(self.url)
        with client.login(user_with_person):
            result = client.query(
                self.QUERY,
                variables={"filters": {"id": {"exact": to_base64("TeamType", expected_team_type.id)}}},
            )

        assert isinstance(result, Response)

        assert result.errors is None
        assert result.data == {
            "teamTypes": {
                "edges": [
                    {
                        "node": {
                            "id": to_base64("TeamType", expected_team_type.id),
                            "displayName": expected_team_type.name,
                        }
                    }
                ],
                "totalCount": 1,
            }
        }
