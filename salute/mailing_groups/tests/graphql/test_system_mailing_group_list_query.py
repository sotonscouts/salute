import pytest
from django.conf import settings
from django.test import override_settings
from django.urls import reverse
from strawberry.relay import to_base64
from strawberry_django.test.client import Response, TestClient

from salute.accounts.models import User
from salute.integrations.workspace.factories import WorkspaceGroupFactory
from salute.mailing_groups.factories import SystemMailingGroupFactory
from salute.roles.factories import DistrictTeamFactory


@pytest.mark.django_db
class TestSystemMailingGroupListQuery:
    url = reverse("graphql")

    QUERY = """
    query listSystemMailingGroups($filters: SystemMailingGroupFilter) {
        systemMailingGroups(filters: $filters) {
            totalCount
            edges {
                node {
                    id
                    displayName
                    shortName
                    address
                }
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
                "message": "You don't have permission to list system mailing groups.",
                "locations": [{"line": 3, "column": 9}],
                "path": ["systemMailingGroups"],
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
                "message": "You don't have permission to list system mailing groups.",
                "locations": [{"line": 3, "column": 9}],
                "path": ["systemMailingGroups"],
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
            "systemMailingGroups": {
                "edges": [],
                "totalCount": 0,
            }
        }

    @override_settings(GOOGLE_DOMAIN="example.com")
    def test_query(self, user_with_person: User) -> None:
        system_mailing_groups = SystemMailingGroupFactory.create_batch(size=10)
        for system_mailing_group in system_mailing_groups:
            WorkspaceGroupFactory(system_mailing_group=system_mailing_group)
        client = TestClient(self.url)
        with client.login(user_with_person):
            result = client.query(
                self.QUERY,
            )

        assert isinstance(result, Response)

        assert result.errors is None
        assert result.data == {
            "systemMailingGroups": {
                "edges": [
                    {
                        "node": {
                            "id": to_base64("SystemMailingGroup", system_mailing_group.id),
                            "displayName": system_mailing_group.display_name,
                            "shortName": system_mailing_group.short_name,
                            "address": f"{system_mailing_group.name}@{settings.GOOGLE_DOMAIN}",  # type: ignore[misc]
                        }
                    }
                    for system_mailing_group in sorted(
                        system_mailing_groups, key=lambda system_mailing_group: system_mailing_group.name
                    )  # noqa: E501
                ],
                "totalCount": 10,
            }
        }

    @override_settings(GOOGLE_DOMAIN="example.com")
    def test_query__filter_by_team(self, user_with_person: User) -> None:
        team = DistrictTeamFactory()
        system_mailing_group = SystemMailingGroupFactory()
        system_mailing_group.teams.add(team)
        WorkspaceGroupFactory(system_mailing_group=system_mailing_group)
        client = TestClient(self.url)
        with client.login(user_with_person):
            result = client.query(
                self.QUERY, variables={"filters": {"teams": {"id": {"exact": to_base64("Team", team.id)}}}}
            )

        assert isinstance(result, Response)

        assert result.errors is None
        assert result.data == {
            "systemMailingGroups": {
                "edges": [
                    {
                        "node": {
                            "id": to_base64("SystemMailingGroup", system_mailing_group.id),
                            "displayName": system_mailing_group.display_name,
                            "shortName": system_mailing_group.short_name,
                            "address": f"{system_mailing_group.name}@{settings.GOOGLE_DOMAIN}",  # type: ignore[misc]
                        }
                    }
                ],
                "totalCount": 1,
            }
        }
