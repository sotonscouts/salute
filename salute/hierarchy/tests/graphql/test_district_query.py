import pytest
from django.urls import reverse
from strawberry_django.test.client import Response, TestClient

from salute.accounts.models import DistrictUserRole, DistrictUserRoleType, User
from salute.hierarchy.factories import DistrictFactory, DistrictSectionFactory, GroupFactory, GroupSectionFactory
from salute.roles.factories import DistrictTeamFactory, RoleFactory


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

    def test_query__summary_stats(self, user_with_person: User) -> None:
        district = DistrictFactory()

        GroupSectionFactory.create_batch(size=5, group__district=district)
        DistrictSectionFactory.create_batch(size=5, district=district)
        RoleFactory.create_batch(size=15, team__district=district)

        client = TestClient(self.url)
        with client.login(user_with_person):
            results = client.query(
                """
                {
                    district {
                        totalGroupsCount
                        totalPeopleCount
                        totalRolesCount
                        totalSectionsCount
                    }
                }
                """
            )

        assert isinstance(results, Response)

        assert results.errors is None
        assert results.data == {
            "district": {
                "totalGroupsCount": 5,
                "totalPeopleCount": 16,
                "totalRolesCount": 15,
                "totalSectionsCount": 10,
            }
        }


@pytest.mark.django_db
class TestDistrictTSADetailsLinkQuery:
    url = reverse("graphql")

    QUERY = """
    {
        district {
            tsaDetailsLink
        }
    }
    """

    @pytest.mark.usefixtures("use_dummy_tsa_unit_link_template")
    def test_query_tsa_profile_link(self, user_with_person: User) -> None:
        district = DistrictFactory()

        client = TestClient(self.url)
        with client.login(user_with_person):
            results = client.query(
                self.QUERY,
            )

        assert isinstance(results, Response)

        assert results.errors is None
        assert results.data == {
            "district": {
                "tsaDetailsLink": f"https://example.com/units/{district.tsa_id}/",
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
                        for g in sorted(groups, key=lambda g: (g.locality.name, g.local_unit_number))  # Default sort
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
                        groups(ordering: [{localUnitNumber: ASC}]){
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
                        groups(ordering: [{localUnitNumber: DESC}]){
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


@pytest.mark.django_db
class TestDistrictJoinTeamsQuery:
    url = reverse("graphql")

    QUERY = """
    query DistrictWithTeams {
        district {
            shortcode
            teams {
                displayName
            }
        }
    }
    """

    def test_query_sections__none(self, user_with_person: User) -> None:
        district = DistrictFactory()
        client = TestClient(self.url)
        with client.login(user_with_person):
            result = client.query(
                self.QUERY,
            )

        assert isinstance(result, Response)

        assert result.errors is None
        assert result.data == {
            "district": {
                "shortcode": district.shortcode,
                "teams": [],
            }
        }

    def test_query_teams(self, user_with_person: User) -> None:
        district = DistrictFactory()
        DistrictUserRole.objects.create(user=user_with_person, district=district, level=DistrictUserRoleType.MANAGER)

        teams = DistrictTeamFactory.create_batch(size=5, district=district)
        client = TestClient(self.url)
        with client.login(user_with_person):
            result = client.query(
                self.QUERY,
            )

        assert isinstance(result, Response)

        assert result.errors is None
        assert result.data == {
            "district": {
                "shortcode": district.shortcode,
                "teams": [{"displayName": t.display_name} for t in sorted(teams, key=lambda t: t.team_type.name)],
            }
        }
