import pytest
from django.urls import reverse
from strawberry.relay import to_base64
from strawberry_django.test.client import Response, TestClient

from salute.accounts.models import User
from salute.hierarchy.constants import GroupType
from salute.hierarchy.factories import DistrictFactory, GroupFactory, GroupSectionFactory


@pytest.mark.django_db
class TestGroupListQuery:
    url = reverse("graphql")

    QUERY = """
    query {
        groups(ordering: [{localUnitNumber: ASC}]) {
            edges {
                node {
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
                "message": "You don't have permission to list groups.",
                "locations": [{"line": 3, "column": 9}],
                "path": ["groups"],
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
                "message": "You don't have permission to list groups.",
                "locations": [{"line": 3, "column": 9}],
                "path": ["groups"],
            }
        ]
        assert results.data is None

    def test_query(self, user_with_person: User) -> None:
        district = DistrictFactory()
        groups = GroupFactory.create_batch(size=5, district=district)
        client = TestClient(self.url)
        with client.login(user_with_person):
            result = client.query(
                self.QUERY,
            )

        assert isinstance(result, Response)

        assert result.errors is None
        assert result.data == {
            "groups": {
                "edges": [
                    {
                        "node": {
                            "id": to_base64("Group", group.id),
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
                    for group in groups
                ],
                "totalCount": 5,
            }
        }

    @pytest.mark.parametrize(
        ("ordering", "reverse"),
        [
            pytest.param("ASC", False, id="asc"),
            pytest.param("DESC", True, id="desc"),
        ],
    )
    def test_query__ordering__unit_number(self, *, ordering: str, reverse: bool, user_with_person: User) -> None:
        district = DistrictFactory()
        groups = GroupFactory.create_batch(size=5, district=district)
        client = TestClient(self.url)
        with client.login(user_with_person):
            result = client.query(
                """
                query groupOrderTest($order: Ordering!) {
                    groups (ordering: [{localUnitNumber: $order}]) {
                        edges {
                            node {
                                unitName
                                ordinal
                            }
                        }
                    }
                }
                """,
                variables={"order": ordering},  # type: ignore[dict-item]
            )

        assert isinstance(result, Response)

        assert result.errors is None
        assert result.data == {
            "groups": {
                "edges": [
                    {
                        "node": {
                            "unitName": group.unit_name,
                            "ordinal": group.ordinal,
                        }
                    }
                    for group in sorted(groups, key=lambda g: g.local_unit_number, reverse=reverse)
                ],
            }
        }

    @pytest.mark.parametrize("group_type", GroupType)
    def test_query__filter__group_type(self, group_type: GroupType, user_with_person: User) -> None:
        district = DistrictFactory()
        groups = {gt: GroupFactory.create_batch(size=5, district=district, group_type=gt) for gt in GroupType}
        client = TestClient(self.url)
        with client.login(user_with_person):
            result = client.query(
                """
                query groupOrderTest($groupType: GroupType!) {
                    groups (filters: {groupType: $groupType}) {
                        edges {
                            node {
                                unitName
                                ordinal
                            }
                        }
                    }
                }
                """,
                variables={"groupType": group_type.upper()},  # type: ignore[dict-item]
            )

        assert isinstance(result, Response)

        assert result.errors is None
        assert result.data == {
            "groups": {
                "edges": [
                    {
                        "node": {
                            "unitName": group.unit_name,
                            "ordinal": group.ordinal,
                        }
                    }
                    for group in sorted(groups[group_type], key=lambda g: (g.locality.name, g.local_unit_number))
                    if group.group_type == str(group_type)
                ],
            }
        }


@pytest.mark.django_db
class TestGroupJoinSectionsQuery:
    url = reverse("graphql")

    QUERY = """
    query {
        groups (filters: {groupType: SEA}){
            edges {
                node {
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
            totalCount
        }
    }
    """

    def test_query_sections__none(self, user_with_person: User) -> None:
        group = GroupFactory(group_type=GroupType.SEA)
        client = TestClient(self.url)
        with client.login(user_with_person):
            result = client.query(
                self.QUERY,
            )

        assert isinstance(result, Response)

        assert result.errors is None
        assert result.data == {
            "groups": {
                "edges": [
                    {
                        "node": {
                            "shortcode": group.shortcode,
                            "sections": {
                                "edges": [],
                                "totalCount": 0,
                            },
                        }
                    }
                ],
                "totalCount": 1,
            }
        }

    def test_query_sections(self, user_with_person: User) -> None:
        group = GroupFactory(group_type=GroupType.SEA)
        sections = GroupSectionFactory.create_batch(size=5, group=group)
        _other_sections = GroupSectionFactory.create_batch(
            size=5, group__district=group.district, group__group_type=GroupType.AIR
        )
        client = TestClient(self.url)
        with client.login(user_with_person):
            result = client.query(
                self.QUERY,
            )

        assert isinstance(result, Response)

        assert result.errors is None
        assert result.data == {
            "groups": {
                "edges": [
                    {
                        "node": {
                            "shortcode": group.shortcode,
                            "sections": {
                                "edges": [
                                    {"node": {"__typename": "GroupSection", "unitName": section.unit_name}}
                                    for section in sorted(sections, key=lambda s: s.id)
                                ],
                                "totalCount": 5,
                            },
                        }
                    }
                ],
                "totalCount": 1,
            }
        }
