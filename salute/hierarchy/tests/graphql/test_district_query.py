import pytest
from django.urls import reverse
from strawberry_django.test.client import Response, TestClient

from salute.accounts.models import User
from salute.hierarchy.factories import DistrictFactory, DistrictSectionFactory, GroupFactory, GroupSectionFactory


@pytest.mark.django_db
class TestDistrictQuery:
    url = reverse("graphql")

    QUERY = """
    query {
        district {
            unitName
            displayName
            shortcode
        }
    }
    """

    def test_query__not_authenticated(self) -> None:
        client = TestClient(self.url)
        results = client.query(self.QUERY, assert_no_errors=False)

        assert isinstance(results, Response)

        assert results.errors == [
            {
                "message": "You don't have permission to view the district.",
                "locations": [{"line": 3, "column": 9}],
                "path": ["district"],
            }
        ]
        assert results.data is None

    def test_query__no_permission(self, user: User) -> None:
        client = TestClient(self.url)
        with client.login(user):
            results = client.query(self.QUERY, assert_no_errors=False)

        assert isinstance(results, Response)

        assert results.errors == [
            {
                "message": "You don't have permission to view the district.",
                "locations": [{"line": 3, "column": 9}],
                "path": ["district"],
            }
        ]
        assert results.data is None

    def test_query__no_district(self, user_with_person: User) -> None:
        """This should not happen in production. There must always be exactly one district."""
        client = TestClient(self.url)
        with client.login(user_with_person):
            result = client.query(self.QUERY, assert_no_errors=False)

        assert isinstance(result, Response)

        assert result.data is None
        assert result.errors == [
            {
                "locations": [{"column": 9, "line": 3}],
                "message": "District matching query does not exist.",
                "path": ["district"],
            }
        ]

    def test_query__two_district(self, user_with_person: User) -> None:
        """This should not happen in production. There must always be exactly one district."""
        DistrictFactory.create_batch(size=2)
        client = TestClient(self.url)
        with client.login(user_with_person):
            result = client.query(self.QUERY, assert_no_errors=False)

        assert isinstance(result, Response)

        assert result.data is None
        assert result.errors == [
            {
                "locations": [{"column": 9, "line": 3}],
                "message": "get() returned more than one District -- it returned 2!",
                "path": ["district"],
            }
        ]

    def test_query(self, user_with_person: User) -> None:
        district = DistrictFactory()
        client = TestClient(self.url)
        with client.login(user_with_person):
            result = client.query(self.QUERY)

        assert isinstance(result, Response)

        assert result.errors is None
        assert result.data == {
            "district": {
                "displayName": district.unit_name,  # This is the same as the unit name currently.
                "shortcode": district.shortcode,
                "unitName": district.unit_name,
            }
        }


@pytest.mark.django_db
class TestDistrictJoinGroupsQuery:
    url = reverse("graphql")

    QUERY = """
    query DistrictWithGroups {
        district {
            shortcode
            groups {
                edges {
                    node {
                        unitName
                        ordinal
                    }
                }
                totalCount
            }
        }
    }
    """

    def test_query_groups__none(self, user_with_person: User) -> None:
        district = DistrictFactory()
        client = TestClient(self.url)
        with client.login(user_with_person):
            result = client.query(self.QUERY)

        assert isinstance(result, Response)

        assert result.errors is None
        assert result.data == {
            "district": {
                "shortcode": district.shortcode,
                "groups": {
                    "edges": [],
                    "totalCount": 0,
                },
            }
        }

    def test_query_groups(self, user_with_person: User) -> None:
        district = DistrictFactory()
        groups = GroupFactory.create_batch(size=5, district=district)
        client = TestClient(self.url)
        with client.login(user_with_person):
            result = client.query(self.QUERY)

        assert isinstance(result, Response)

        assert result.errors is None
        assert result.data == {
            "district": {
                "shortcode": district.shortcode,
                "groups": {
                    "edges": [
                        {"node": {"ordinal": g.ordinal, "unitName": g.unit_name}}
                        for g in sorted(groups, key=lambda g: g.local_unit_number)  # Default sort
                    ],
                    "totalCount": 5,
                },
            }
        }

    def test_query_groups__ordering__local_unit_number_asc(self, user_with_person: User) -> None:
        district = DistrictFactory()
        groups = GroupFactory.create_batch(size=5, district=district)
        client = TestClient(self.url)
        with client.login(user_with_person):
            result = client.query(
                """
                query DistrictWithGroups {
                    district {
                        shortcode
                        groups(order: {localUnitNumber: ASC}){
                            edges {
                                node {
                                    unitName
                                    ordinal
                                }
                            }
                            totalCount
                        }
                    }
                }
                """
            )

        assert isinstance(result, Response)

        assert result.errors is None
        assert result.data == {
            "district": {
                "shortcode": district.shortcode,
                "groups": {
                    "edges": [
                        {"node": {"ordinal": g.ordinal, "unitName": g.unit_name}}
                        for g in sorted(groups, key=lambda g: g.local_unit_number)
                    ],
                    "totalCount": 5,
                },
            }
        }

    def test_query_groups__ordering__local_unit_number_desc(self, user_with_person: User) -> None:
        district = DistrictFactory()
        groups = GroupFactory.create_batch(size=5, district=district)
        client = TestClient(self.url)
        with client.login(user_with_person):
            result = client.query(
                """
                query DistrictWithGroups {
                    district {
                        shortcode
                        groups(order: {localUnitNumber: DESC}){
                            edges {
                                node {
                                    unitName
                                    ordinal
                                }
                            }
                            totalCount
                        }
                    }
                }
                """
            )

        assert isinstance(result, Response)

        assert result.errors is None
        assert result.data == {
            "district": {
                "shortcode": district.shortcode,
                "groups": {
                    "edges": [
                        {"node": {"ordinal": g.ordinal, "unitName": g.unit_name}}
                        for g in sorted(groups, key=lambda g: g.local_unit_number, reverse=True)
                    ],
                    "totalCount": 5,
                },
            }
        }


@pytest.mark.django_db
class TestDistrictJoinAllSectionsQuery:
    url = reverse("graphql")

    QUERY = """
    query DistrictWithSections {
        district {
            shortcode
            sections {
                edges {
                    node {
                        unitName
                    }
                }
                totalCount
            }
        }
    }
    """

    def test_query_sections__none(self, user_with_person: User) -> None:
        district = DistrictFactory()
        client = TestClient(self.url)
        with client.login(user_with_person):
            result = client.query(self.QUERY)

        assert isinstance(result, Response)

        assert result.errors is None
        assert result.data == {
            "district": {
                "shortcode": district.shortcode,
                "sections": {
                    "edges": [],
                    "totalCount": 0,
                },
            }
        }

    def test_query_groups(self, user_with_person: User) -> None:
        district = DistrictFactory()
        sections = GroupSectionFactory.create_batch(
            size=5, group__district=district
        ) + DistrictSectionFactory.create_batch(size=5, district=district)
        client = TestClient(self.url)
        with client.login(user_with_person):
            result = client.query(self.QUERY)

        assert isinstance(result, Response)

        assert result.errors is None
        assert result.data == {
            "district": {
                "shortcode": district.shortcode,
                "sections": {
                    "edges": [
                        {"node": {"unitName": s.unit_name}}
                        for s in sorted(sections, key=lambda s: s.id)  # Default sort
                        if s.district is not None  # Should be filtered to just district sections
                    ],
                    "totalCount": 5,
                },
            }
        }
