from uuid import UUID

import pytest
from django.urls import reverse
from strawberry.relay import to_base64
from strawberry_django.test.client import Response, TestClient

from salute.accounts.models import User
from salute.roles.factories import TeamTypeFactory


@pytest.mark.django_db
class TestTeamTypeQuery:
    url = reverse("graphql")

    QUERY = """
    query getTeamType($teamTypeId: ID!) {
        teamType(teamTypeId: $teamTypeId) {
            id
            displayName
        }
    }
    """

    def test_query__not_authenticated(self) -> None:
        team_type = TeamTypeFactory()
        client = TestClient(self.url)
        results = client.query(
            self.QUERY,
            variables={"teamTypeId": to_base64("TeamType", team_type.id)},  # type: ignore[dict-item]
            assert_no_errors=False,
        )

        assert isinstance(results, Response)

        assert results.errors == [
            {
                "message": "You don't have permission to view that team type.",
                "locations": [{"line": 3, "column": 9}],
                "path": ["teamType"],
            }
        ]
        assert results.data is None

    def test_query__no_permission(self, user: User) -> None:
        team_type = TeamTypeFactory()
        client = TestClient(self.url)
        with client.login(user):
            results = client.query(
                self.QUERY,
                variables={"teamTypeId": to_base64("TeamType", team_type.id)},  # type: ignore[dict-item]
                assert_no_errors=False,
            )

        assert isinstance(results, Response)

        assert results.errors == [
            {
                "message": "You don't have permission to view that team type.",
                "locations": [{"line": 3, "column": 9}],
                "path": ["teamType"],
            }
        ]
        assert results.data is None

    def test_query(self, user_with_person: User) -> None:
        team_type = TeamTypeFactory()
        client = TestClient(self.url)
        with client.login(user_with_person):
            result = client.query(
                self.QUERY,
                variables={"teamTypeId": to_base64("TeamType", team_type.id)},  # type: ignore[dict-item]
            )

        assert isinstance(result, Response)

        assert result.errors is None
        assert result.data == {
            "teamType": {
                "id": to_base64("TeamType", team_type.id),
                "displayName": team_type.name,
            }
        }

    def test_query__nickname(self, user_with_person: User) -> None:
        """Test that the nickname appears transparently as the display name"""
        team_type = TeamTypeFactory(nickname="Bees")
        client = TestClient(self.url)
        with client.login(user_with_person):
            result = client.query(
                self.QUERY,
                variables={"teamTypeId": to_base64("TeamType", team_type.id)},  # type: ignore[dict-item]
            )

        assert isinstance(result, Response)

        assert result.errors is None
        assert result.data == {
            "teamType": {
                "id": to_base64("TeamType", team_type.id),
                "displayName": "Bees",
            }
        }

    def test_query__not_found(self, user_with_person: User) -> None:
        client = TestClient(self.url)
        with client.login(user_with_person):
            result = client.query(
                self.QUERY,
                variables={"teamTypeId": to_base64("TeamType", UUID(int=0))},  # type: ignore[dict-item]
                assert_no_errors=False,
            )

        assert isinstance(result, Response)

        assert result.errors == [
            {
                "locations": [{"column": 9, "line": 3}],
                "message": "TeamType matching query does not exist.",
                "path": ["teamType"],
            }
        ]
        assert result.data is None
