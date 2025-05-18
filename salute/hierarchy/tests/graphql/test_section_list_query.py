import pytest
from django.urls import reverse
from strawberry.relay import to_base64
from strawberry_django.test.client import Response, TestClient

from salute.accounts.models import User
from salute.hierarchy.constants import DISTRICT_SECTION_TYPES, GROUP_SECTION_TYPES, SectionType, Weekday
from salute.hierarchy.factories import DistrictFactory, DistrictSectionFactory, GroupSectionFactory
from salute.hierarchy.models import Section


@pytest.mark.django_db
class TestSectionListQuery:
    url = reverse("graphql")

    QUERY = """
    query {
        sections {
            edges {
                node {
                    id
                    unitName
                    shortcode
                    displayName
                    usualWeekday
                    district {
                        unitName
                    }
                    group {
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
                "message": "You don't have permission to list sections.",
                "locations": [{"line": 3, "column": 9}],
                "path": ["sections"],
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
                "message": "You don't have permission to list sections.",
                "locations": [{"line": 3, "column": 9}],
                "path": ["sections"],
            }
        ]
        assert results.data is None

    def test_query__district(self, user_with_person: User) -> None:
        district = DistrictFactory()
        sections = DistrictSectionFactory.create_batch(size=5, district=district)
        client = TestClient(self.url)
        with client.login(user_with_person):
            result = client.query(
                self.QUERY,
            )

        assert isinstance(result, Response)

        assert result.errors is None
        assert result.data == {
            "sections": {
                "edges": [
                    {
                        "node": {
                            "id": to_base64("DistrictOrGroupSection", section.id),
                            "displayName": section.display_name,
                            "shortcode": section.shortcode,
                            "unitName": section.unit_name,
                            "usualWeekday": section.usual_weekday.name,
                            "district": {
                                "unitName": section.district.unit_name,
                            },
                            "group": None,
                        }
                    }
                    for section in sorted(sections, key=lambda s: s.id)
                ],
                "totalCount": 5,
            }
        }

    def test_query__group(self, user_with_person: User) -> None:
        district = DistrictFactory()
        sections = GroupSectionFactory.create_batch(size=5, group__district=district)
        client = TestClient(self.url)
        with client.login(user_with_person):
            result = client.query(
                self.QUERY,
            )

        assert isinstance(result, Response)

        assert result.errors is None
        assert result.data == {
            "sections": {
                "edges": [
                    {
                        "node": {
                            "id": to_base64("DistrictOrGroupSection", section.id),
                            "displayName": section.display_name,
                            "shortcode": section.shortcode,
                            "unitName": section.unit_name,
                            "usualWeekday": section.usual_weekday.name,
                            "group": {
                                "unitName": section.group.unit_name,
                            },
                            "district": None,
                        }
                    }
                    for section in sorted(sections, key=lambda s: s.id)
                ],
                "totalCount": 5,
            }
        }

    def test_query__mixed(self, user_with_person: User) -> None:
        district = DistrictFactory()
        district_sections = DistrictSectionFactory.create_batch(size=5, district=district)
        group_sections = GroupSectionFactory.create_batch(size=5, group__district=district)
        client = TestClient(self.url)
        with client.login(user_with_person):
            result = client.query(
                self.QUERY,
            )

        assert isinstance(result, Response)

        assert result.errors is None
        assert result.data == {
            "sections": {
                "edges": [
                    {
                        "node": {
                            "id": to_base64("DistrictOrGroupSection", section.id),
                            "displayName": section.display_name,
                            "shortcode": section.shortcode,
                            "unitName": section.unit_name,
                            "usualWeekday": section.usual_weekday.name,
                            "group": {
                                "unitName": section.group.unit_name,
                            },
                            "district": None,
                        }
                    }
                    if section.group is not None
                    else {
                        "node": {
                            "id": to_base64("DistrictOrGroupSection", section.id),
                            "displayName": section.display_name,
                            "shortcode": section.shortcode,
                            "unitName": section.unit_name,
                            "usualWeekday": section.usual_weekday.name,
                            "district": {
                                "unitName": section.district.unit_name,
                            },
                            "group": None,
                        }
                    }
                    for section in sorted(district_sections + group_sections, key=lambda s: s.id)
                ],
                "totalCount": 10,
            }
        }

    @pytest.mark.parametrize(
        ("ordering", "reverse"),
        [
            pytest.param("ASC", False, id="asc"),
            pytest.param("DESC", True, id="desc"),
        ],
    )
    def test_query__ordering__section_type(self, *, ordering: str, reverse: bool, user_with_person: User) -> None:
        district = DistrictFactory()
        _group_sections = [
            GroupSectionFactory(group__district=district, section_type=section_type)
            for section_type in GROUP_SECTION_TYPES
        ]
        _district_sections = [
            DistrictSectionFactory(district=district, section_type=section_type)
            for section_type in DISTRICT_SECTION_TYPES
        ]
        client = TestClient(self.url)
        with client.login(user_with_person):
            result = client.query(
                """
                query sectionOrderTest($order: Ordering!) {
                    sections (ordering: [{sectionType: $order}]) {
                        edges {
                            node {
                                sectionTypeInfo {
                                    value
                                }
                            }
                        }
                    }
                }
                """,
                variables={"order": ordering},  # type: ignore[dict-item]
            )

        assert isinstance(result, Response)

        expected = reversed(SectionType) if reverse else SectionType

        assert result.errors is None
        assert result.data == {
            "sections": {
                "edges": [
                    {
                        "node": {
                            "sectionTypeInfo": {
                                "value": section_type.name,
                            }
                        }
                    }
                    for section_type in expected
                ],
            }
        }

    @pytest.mark.parametrize(
        ("ordering", "reverse"),
        [
            pytest.param("ASC", False, id="asc"),
            pytest.param("DESC", True, id="desc"),
        ],
    )
    def test_query__ordering__usual_weekday(self, *, ordering: str, reverse: bool, user_with_person: User) -> None:
        district = DistrictFactory()
        _group_sections = [GroupSectionFactory(group__district=district, usual_weekday=weekday) for weekday in Weekday]
        client = TestClient(self.url)
        with client.login(user_with_person):
            result = client.query(
                """
                query sectionOrderTest($order: Ordering!) {
                    sections (ordering: [{usualWeekday: $order}]) {
                        edges {
                            node {
                                usualWeekday
                            }
                        }
                    }
                }
                """,
                variables={"order": ordering},  # type: ignore[dict-item]
            )

        assert isinstance(result, Response)

        expected = reversed(Weekday) if reverse else Weekday

        assert result.errors is None
        assert result.data == {
            "sections": {
                "edges": [
                    {
                        "node": {
                            "usualWeekday": weekday.name,
                        }
                    }
                    for weekday in expected
                ],
            }
        }

    @pytest.mark.parametrize(
        ("ordering", "reverse"),
        [
            pytest.param("ASC", False, id="asc"),
            pytest.param("DESC", True, id="desc"),
        ],
    )
    def test_query__ordering__group__local_unit_number(
        self, *, ordering: str, reverse: bool, user_with_person: User
    ) -> None:
        district = DistrictFactory()
        _group_sections = [
            GroupSectionFactory(group__district=district, section_type=section_type)
            for section_type in GROUP_SECTION_TYPES
        ]
        _district_sections = [
            DistrictSectionFactory(district=district, section_type=section_type)
            for section_type in DISTRICT_SECTION_TYPES
        ]
        client = TestClient(self.url)
        with client.login(user_with_person):
            result = client.query(
                """
                query sectionOrderTest($order: Ordering!) {
                    sections (ordering: [{group: {localUnitNumber: $order}}]) {
                        edges {
                            node {
                                unitName
                                group {
                                    ordinal
                                }
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
            "sections": {
                "edges": [
                    {
                        "node": {
                            "unitName": section.unit_name,
                            "group": {
                                "ordinal": section.group.ordinal,
                            }
                            if section.group
                            else None,
                        }
                    }
                    for section in sorted(
                        _group_sections + _district_sections,
                        key=lambda s: s.group.local_unit_number if s.group else 0,
                        reverse=reverse,
                    )
                ],
            }
        }

    def test_query__filter__section_type(self, user_with_person: User) -> None:
        district = DistrictFactory()
        _group_sections = [
            GroupSectionFactory(group__district=district, section_type=section_type)
            for section_type in GROUP_SECTION_TYPES
        ]
        _district_sections = [
            DistrictSectionFactory(district=district, section_type=section_type)
            for section_type in DISTRICT_SECTION_TYPES
        ]
        client = TestClient(self.url)
        with client.login(user_with_person):
            result = client.query(
                """
                query groupOrderTest($sectionType: SectionType!) {
                    sections (filters: {sectionType: {exact: $sectionType}}) {
                        edges {
                            node {
                                unitName
                                sectionTypeInfo {
                                    value
                                }
                            }
                        }
                    }
                }
                """,
                variables={"sectionType": SectionType.BEAVERS.name},  # type: ignore[dict-item]
            )

        assert isinstance(result, Response)

        assert result.errors is None
        assert result.data == {
            "sections": {
                "edges": [
                    {
                        "node": {
                            "unitName": Section.objects.get(section_type=SectionType.BEAVERS).unit_name,
                            "sectionTypeInfo": {
                                "value": "BEAVERS",
                            },
                        }
                    }
                ],
            }
        }

    def test_query__filter__weekday(self, user_with_person: User) -> None:
        district = DistrictFactory()
        _group_sections = [GroupSectionFactory(group__district=district, usual_weekday=weekday) for weekday in Weekday]
        client = TestClient(self.url)
        with client.login(user_with_person):
            result = client.query(
                """
                query groupOrderTest($usualWeekday: [Weekday!]!) {
                    sections (filters: {usualWeekday: {inList: $usualWeekday}}, ordering: [{usualWeekday: ASC}]) {
                        edges {
                            node {
                                unitName
                                usualWeekday
                            }
                        }
                    }
                }
                """,
                variables={"usualWeekday": [Weekday.FRIDAY.name, Weekday.SATURDAY.name]},  # type: ignore[dict-item]
            )

        assert isinstance(result, Response)

        assert result.errors is None
        assert result.data == {
            "sections": {
                "edges": [
                    {
                        "node": {
                            "unitName": Section.objects.get(usual_weekday=Weekday.FRIDAY).unit_name,
                            "usualWeekday": "FRIDAY",
                        }
                    },
                    {
                        "node": {
                            "unitName": Section.objects.get(usual_weekday=Weekday.SATURDAY).unit_name,
                            "usualWeekday": "SATURDAY",
                        }
                    },
                ],
            }
        }
