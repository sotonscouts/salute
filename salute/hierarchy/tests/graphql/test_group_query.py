from uuid import UUID

import pytest
from django.urls import reverse
from strawberry.relay import to_base64
from strawberry_django.test.client import Response, TestClient

from salute.accounts.models import DistrictUserRole, DistrictUserRoleType, User
from salute.hierarchy.factories import DistrictFactory, GroupFactory, GroupSectionFactory
from salute.roles.factories import GroupTeamFactory


@pytest.mark.django_db
class TestGroupQuery:
    url = reverse("graphql")

    QUERY = """
    query getGroup($groupId: GlobalID!) {
        group(groupId: $groupId) {
            id
            unitName
            shortcode
            displayName
            charityNumber
            ordinal
            district {
                unitName
            }
        }
    }
    """

    def test_query__not_authenticated(self) -> None:
        group = GroupFactory()
        group_id = to_base64("Group", group.id)
        client = TestClient(self.url)
        results = client.query(
            self.QUERY,
            variables={"groupId": group_id},  # type: ignore[dict-item]
            assert_no_errors=False,
        )

        assert isinstance(results, Response)

        assert results.errors == [
            {
                "message": "You don't have permission to view that group.",
                "locations": [{"line": 3, "column": 9}],
                "path": ["group"],
            }
        ]
        assert results.data is None

    def test_query__no_permission(self, user: User) -> None:
        group = GroupFactory()
        group_id = to_base64("Group", group.id)
        client = TestClient(self.url)
        with client.login(user):
            results = client.query(
                self.QUERY,
                variables={"groupId": group_id},  # type: ignore[dict-item]
                assert_no_errors=False,
            )

        assert isinstance(results, Response)

        assert results.errors == [
            {
                "message": "You don't have permission to view that group.",
                "locations": [{"line": 3, "column": 9}],
                "path": ["group"],
            }
        ]
        assert results.data is None

    def test_query__no_group(self, user_with_person: User) -> None:
        """This should not happen in production. There must always be exactly one district."""
        group_id = to_base64("Group", UUID(int=0))
        client = TestClient(self.url)
        with client.login(user_with_person):
            result = client.query(
                self.QUERY,
                variables={"groupId": group_id},  # type: ignore[dict-item]
                assert_no_errors=False,
            )

        assert isinstance(result, Response)

        assert result.data is None
        assert result.errors == [
            {
                "locations": [{"column": 9, "line": 3}],
                "message": "Group matching query does not exist.",
                "path": ["group"],
            }
        ]

    def test_query(self, user_with_person: User) -> None:
        group = GroupFactory()
        group_id = to_base64("Group", group.id)
        client = TestClient(self.url)
        with client.login(user_with_person):
            result = client.query(
                self.QUERY,
                variables={"groupId": group_id},  # type: ignore[dict-item]
                assert_no_errors=False,
            )

        assert isinstance(result, Response)

        assert result.errors is None
        assert result.data == {
            "group": {
                "id": group_id,
                "displayName": group.display_name,
                "shortcode": group.shortcode,
                "unitName": group.unit_name,
                "charityNumber": group.charity_number,
                "district": {
                    "unitName": group.district.unit_name,
                },
                "ordinal": group.ordinal,
            }
        }


@pytest.mark.django_db
class TestGroupJoinSectionsQuery:
    url = reverse("graphql")

    QUERY = """
    query GroupWithSections($groupId: GlobalID!) {
        group(groupId: $groupId) {
            shortcode
            sections {
                edges {
                    node {
                        __typename
                        unitName
                    }
                }
                totalCount
            }
        }
    }
    """

    def test_query_sections__none(self, user_with_person: User) -> None:
        group = GroupFactory()
        group_id = to_base64("Group", group.id)
        client = TestClient(self.url)
        with client.login(user_with_person):
            result = client.query(
                self.QUERY,
                variables={"groupId": group_id},  # type: ignore[dict-item]
            )

        assert isinstance(result, Response)

        assert result.errors is None
        assert result.data == {
            "group": {
                "shortcode": group.shortcode,
                "sections": {
                    "edges": [],
                    "totalCount": 0,
                },
            }
        }

    def test_query_sections(self, user_with_person: User) -> None:
        group = GroupFactory()
        group_id = to_base64("Group", group.id)
        sections = GroupSectionFactory.create_batch(size=5, group=group)
        client = TestClient(self.url)
        with client.login(user_with_person):
            result = client.query(
                self.QUERY,
                variables={"groupId": group_id},  # type: ignore[dict-item]
            )

        assert isinstance(result, Response)

        assert result.errors is None
        assert result.data == {
            "group": {
                "shortcode": group.shortcode,
                "sections": {
                    "edges": [
                        {
                            "node": {
                                "__typename": "GroupSection",  # Specific type: no district field
                                "unitName": s.unit_name,
                            }
                        }
                        for s in sorted(sections, key=lambda s: s.id)  # Default sort
                    ],
                    "totalCount": 5,
                },
            }
        }


@pytest.mark.django_db
class TestGroupJoinTeamsQuery:
    url = reverse("graphql")

    QUERY = """
    query GroupWithTeams($groupId: GlobalID!) {
        group(groupId: $groupId) {
            shortcode
            teams {
                displayName
            }
        }
    }
    """

    def test_query_sections__none(self, user_with_person: User) -> None:
        group = GroupFactory()
        group_id = to_base64("Group", group.id)
        client = TestClient(self.url)
        with client.login(user_with_person):
            result = client.query(
                self.QUERY,
                variables={"groupId": group_id},  # type: ignore[dict-item]
            )

        assert isinstance(result, Response)

        assert result.errors is None
        assert result.data == {
            "group": {
                "shortcode": group.shortcode,
                "teams": [],
            }
        }

    def test_query_teams(self, user_with_person: User) -> None:
        district = DistrictFactory()
        DistrictUserRole.objects.create(user=user_with_person, district=district, level=DistrictUserRoleType.MANAGER)

        group = GroupFactory(district=district)
        group_id = to_base64("Group", group.id)
        teams = GroupTeamFactory.create_batch(size=5, group=group)
        client = TestClient(self.url)
        with client.login(user_with_person):
            result = client.query(
                self.QUERY,
                variables={"groupId": group_id},  # type: ignore[dict-item]
            )

        assert isinstance(result, Response)

        assert result.errors is None
        assert result.data == {
            "group": {
                "shortcode": group.shortcode,
                "teams": [{"displayName": t.display_name} for t in sorted(teams, key=lambda t: t.team_type.name)],
            }
        }
