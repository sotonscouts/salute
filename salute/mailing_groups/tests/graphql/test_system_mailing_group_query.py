from uuid import UUID

import pytest
from django.conf import settings
from django.test import override_settings
from django.urls import reverse
from strawberry.relay import to_base64
from strawberry_django.test.client import Response, TestClient

from salute.accounts.models import User
from salute.integrations.workspace.factories import WorkspaceGroupFactory
from salute.mailing_groups.factories import SystemMailingGroupFactory


@pytest.mark.django_db
class TestSystemMailingGroupQuery:
    url = reverse("graphql")

    QUERY = """
    query getSystemMailingGroup($systemMailingGroupId: ID!) {
        systemMailingGroup(systemMailingGroupId: $systemMailingGroupId) {
            id
            displayName
            shortName
            address
        }
    }
    """

    def test_query__not_authenticated(self) -> None:
        system_mailing_group = SystemMailingGroupFactory()
        system_mailing_group_id = to_base64("SystemMailingGroup", system_mailing_group.id)
        client = TestClient(self.url)
        results = client.query(
            self.QUERY,
            variables={"systemMailingGroupId": system_mailing_group_id},  # type: ignore[dict-item]
            assert_no_errors=False,
        )

        assert isinstance(results, Response)

        assert results.errors == [
            {
                "message": "You don't have permission to view that mailing group.",
                "locations": [{"line": 3, "column": 9}],
                "path": ["systemMailingGroup"],
            }
        ]
        assert results.data is None

    def test_query__no_permission(self, user: User) -> None:
        system_mailing_group = SystemMailingGroupFactory()
        system_mailing_group_id = to_base64("SystemMailingGroup", system_mailing_group.id)
        client = TestClient(self.url)
        with client.login(user):
            results = client.query(
                self.QUERY,
                variables={"systemMailingGroupId": system_mailing_group_id},  # type: ignore[dict-item]
                assert_no_errors=False,
            )

        assert isinstance(results, Response)

        assert results.errors == [
            {
                "message": "You don't have permission to view that mailing group.",
                "locations": [{"line": 3, "column": 9}],
                "path": ["systemMailingGroup"],
            }
        ]
        assert results.data is None

    def test_query__no_mailing_group(self, user_with_person: User) -> None:
        system_mailing_group_id = to_base64("SystemMailingGroup", UUID(int=0))
        client = TestClient(self.url)
        with client.login(user_with_person):
            result = client.query(
                self.QUERY,
                variables={"systemMailingGroupId": system_mailing_group_id},  # type: ignore[dict-item]
                assert_no_errors=False,
            )

        assert isinstance(result, Response)

        assert result.data is None
        assert result.errors == [
            {
                "locations": [{"column": 9, "line": 3}],
                "message": "SystemMailingGroup matching query does not exist.",
                "path": ["systemMailingGroup"],
            }
        ]

    def test_query__no_workspace_group(self, user_with_person: User) -> None:
        system_mailing_group = SystemMailingGroupFactory()
        system_mailing_group_id = to_base64("SystemMailingGroup", system_mailing_group.id)
        client = TestClient(self.url)
        with client.login(user_with_person):
            result = client.query(
                self.QUERY,
                variables={"systemMailingGroupId": system_mailing_group_id},  # type: ignore[dict-item]
                assert_no_errors=False,
            )

        assert isinstance(result, Response)

        assert result.data is None
        assert result.errors == [
            {
                "locations": [{"column": 9, "line": 3}],
                "message": "SystemMailingGroup matching query does not exist.",
                "path": ["systemMailingGroup"],
            }
        ]

    @override_settings(GOOGLE_DOMAIN="example.com")
    def test_query(self, user_with_person: User) -> None:
        system_mailing_group = SystemMailingGroupFactory()
        WorkspaceGroupFactory(system_mailing_group=system_mailing_group)
        system_mailing_group_id = to_base64("SystemMailingGroup", system_mailing_group.id)
        client = TestClient(self.url)
        with client.login(user_with_person):
            result = client.query(
                self.QUERY,
                variables={"systemMailingGroupId": system_mailing_group_id},  # type: ignore[dict-item]
                assert_no_errors=False,
            )

        assert isinstance(result, Response)

        assert result.data == {
            "systemMailingGroup": {
                "id": system_mailing_group_id,
                "displayName": system_mailing_group.display_name,
                "shortName": system_mailing_group.short_name,
                "address": f"{system_mailing_group.name}@{settings.GOOGLE_DOMAIN}",  # type: ignore[misc]
            }
        }
