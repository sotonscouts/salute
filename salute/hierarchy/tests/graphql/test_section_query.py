from uuid import UUID

import pytest
from django.urls import reverse
from strawberry.relay import to_base64
from strawberry_django.test.client import Response, TestClient

from salute.accounts.models import DistrictUserRole, DistrictUserRoleType, User
from salute.hierarchy.constants import SectionType
from salute.hierarchy.factories import DistrictFactory, DistrictSectionFactory, GroupSectionFactory
from salute.integrations.osm.factories import OSMSectionHeadcountRecordFactory
from salute.roles.factories import GroupSectionTeamFactory


@pytest.mark.django_db
class TestSectionQuery:
    url = reverse("graphql")

    QUERY = """
        query getSection($sectionId: ID!) {
        section(sectionId: $sectionId) {
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
    """

    def test_query__not_authenticated(self) -> None:
        section = GroupSectionFactory()
        section_id = to_base64("Section", section.id)
        client = TestClient(self.url)
        results = client.query(
            self.QUERY,
            variables={"sectionId": section_id},  # type: ignore[dict-item]
            assert_no_errors=False,
        )

        assert isinstance(results, Response)

        assert results.errors == [
            {
                "message": "You don't have permission to view that section.",
                "locations": [{"line": 3, "column": 9}],
                "path": ["section"],
            }
        ]
        assert results.data is None

    def test_query__no_permission(self, user: User) -> None:
        section = GroupSectionFactory()
        section_id = to_base64("Section", section.id)
        client = TestClient(self.url)
        with client.login(user):
            results = client.query(
                self.QUERY,
                variables={"sectionId": section_id},  # type: ignore[dict-item]
                assert_no_errors=False,
            )

        assert isinstance(results, Response)

        assert results.errors == [
            {
                "message": "You don't have permission to view that section.",
                "locations": [{"line": 3, "column": 9}],
                "path": ["section"],
            }
        ]
        assert results.data is None

    def test_query__no_section(self, user_with_person: User) -> None:
        section_id = to_base64("Section", UUID(int=0))
        client = TestClient(self.url)
        with client.login(user_with_person):
            result = client.query(
                self.QUERY,
                variables={"sectionId": section_id},  # type: ignore[dict-item]
                assert_no_errors=False,
            )

        assert isinstance(result, Response)

        assert result.data is None
        assert result.errors == [
            {
                "locations": [{"column": 9, "line": 3}],
                "message": "Section matching query does not exist.",
                "path": ["section"],
            }
        ]

    def test_query__group_section(self, user_with_person: User) -> None:
        section = GroupSectionFactory()
        section_id = to_base64("DistrictOrGroupSection", section.id)
        client = TestClient(self.url)
        with client.login(user_with_person):
            result = client.query(
                self.QUERY,
                variables={"sectionId": section_id},  # type: ignore[dict-item]
                assert_no_errors=False,
            )

        assert isinstance(result, Response)

        assert result.errors is None
        assert result.data == {
            "section": {
                "id": section_id,
                "displayName": section.display_name,
                "shortcode": section.shortcode,
                "unitName": section.unit_name,
                "usualWeekday": section.usual_weekday.name,
                "district": None,
                "group": {
                    "unitName": section.group.unit_name,
                },
            }
        }

    def test_query__district_section(self, user_with_person: User) -> None:
        section = DistrictSectionFactory()
        section_id = to_base64("DistrictOrGroupSection", section.id)
        client = TestClient(self.url)
        with client.login(user_with_person):
            result = client.query(
                self.QUERY,
                variables={"sectionId": section_id},  # type: ignore[dict-item]
                assert_no_errors=False,
            )

        assert isinstance(result, Response)

        assert result.errors is None
        assert result.data == {
            "section": {
                "id": section_id,
                "displayName": section.display_name,
                "shortcode": section.shortcode,
                "unitName": section.unit_name,
                "usualWeekday": section.usual_weekday.name,
                "group": None,
                "district": {
                    "unitName": section.district.unit_name,
                },
            }
        }


@pytest.mark.django_db
class TestSectionYoungPersonCountQuery:
    url = reverse("graphql")

    QUERY = """
    query getSection($sectionId: ID!) {
        section(sectionId: $sectionId) {
            youngPersonCount
        }
    }
    """

    def test_query_young_person_count__none(self, user_with_person: User) -> None:
        section = GroupSectionFactory()
        section_id = to_base64("DistrictOrGroupSection", section.id)
        client = TestClient(self.url)
        with client.login(user_with_person):
            result = client.query(self.QUERY, variables={"sectionId": section_id})  # type: ignore[dict-item]

        assert isinstance(result, Response)

        assert result.errors is None

        assert result.data == {
            "section": {
                "youngPersonCount": None,
            }
        }

    def test_query_young_person_count__no_permission(self, user_with_person: User) -> None:
        section = GroupSectionFactory()
        section_id = to_base64("DistrictOrGroupSection", section.id)
        client = TestClient(self.url)
        with client.login(user_with_person):
            result = client.query(self.QUERY, variables={"sectionId": section_id})  # type: ignore[dict-item]

        assert isinstance(result, Response)

        assert result.errors is None
        assert result.data == {
            "section": {
                "youngPersonCount": None,
            }
        }

    def test_query_young_person_count__with_sections(self, user_with_person: User) -> None:
        district = DistrictFactory()
        DistrictUserRole.objects.create(user=user_with_person, district=district, level=DistrictUserRoleType.MANAGER)
        section = GroupSectionFactory(group__district=district)
        OSMSectionHeadcountRecordFactory(section=section, young_person_count=10)
        section_id = to_base64("DistrictOrGroupSection", section.id)
        client = TestClient(self.url)
        with client.login(user_with_person):
            result = client.query(self.QUERY, variables={"sectionId": section_id})  # type: ignore[dict-item]

        assert isinstance(result, Response)

        assert result.errors is None
        assert result.data == {
            "section": {
                "youngPersonCount": 10,
            }
        }


@pytest.mark.django_db
class TestSectionTypeInfoQuery:
    url = reverse("graphql")

    QUERY = """
        query getSection($sectionId: ID!) {
        section(sectionId: $sectionId) {
                unitName
                sectionTypeInfo {
                    value
                    displayName
                    operatingCategory
                    formattedAgeRange
                }
            }
        }
    """

    def test_query__group_section(self, user_with_person: User) -> None:
        section = GroupSectionFactory(section_type=SectionType.BEAVERS)
        section_id = to_base64("DistrictOrGroupSection", section.id)
        client = TestClient(self.url)
        with client.login(user_with_person):
            result = client.query(
                self.QUERY,
                variables={"sectionId": section_id},  # type: ignore[dict-item]
                assert_no_errors=False,
            )

        assert isinstance(result, Response)

        assert result.errors is None
        assert result.data == {
            "section": {
                "unitName": section.unit_name,
                "sectionTypeInfo": {
                    "value": "BEAVERS",
                    "displayName": "Beavers",
                    "operatingCategory": "GROUP",
                    "formattedAgeRange": "6 - 8 years",
                },
            }
        }

    def test_query__district_section(self, user_with_person: User) -> None:
        section = DistrictSectionFactory(section_type=SectionType.EXPLORERS)
        section_id = to_base64("DistrictOrGroupSection", section.id)
        client = TestClient(self.url)
        with client.login(user_with_person):
            result = client.query(
                self.QUERY,
                variables={"sectionId": section_id},  # type: ignore[dict-item]
                assert_no_errors=False,
            )

        assert isinstance(result, Response)

        assert result.errors is None
        assert result.data == {
            "section": {
                "unitName": section.unit_name,
                "sectionTypeInfo": {
                    "value": "EXPLORERS",
                    "displayName": "Explorers",
                    "operatingCategory": "DISTRICT",
                    "formattedAgeRange": "14 - 18 years",
                },
            }
        }


@pytest.mark.django_db
class TestSectionTSADetailsLinkQuery:
    url = reverse("graphql")

    QUERY = """
    query getSectionTsaDetailsLink($sectionId: ID!) {
        section(sectionId: $sectionId) {
            tsaDetailsLink
        }
    }
    """

    @pytest.mark.usefixtures("use_dummy_tsa_unit_link_template")
    def test_query_tsa_profile_link(self, user_with_person: User) -> None:
        district = DistrictFactory()
        section = GroupSectionFactory(group__district=district)

        section_id = to_base64("DistrictOrGroupSection", section.id)
        client = TestClient(self.url)
        with client.login(user_with_person):
            results = client.query(
                self.QUERY,
                variables={"sectionId": section_id},  # type: ignore[dict-item]
                assert_no_errors=False,
            )

        assert isinstance(results, Response)

        assert results.errors is None
        assert results.data == {
            "section": {
                "tsaDetailsLink": f"https://example.com/units/{section.tsa_id}/",
            }
        }


@pytest.mark.django_db
class TestSectionTeamQuery:
    url = reverse("graphql")

    QUERY = """
        query getSectionTeam($sectionId: ID!) {
        section(sectionId: $sectionId) {
                unitName
                team {
                    displayName
                    teamType {
                        displayName
                    }
                }
            }
        }
    """

    def test_query__team(self, user_with_person: User) -> None:
        district = DistrictFactory()
        DistrictUserRole.objects.create(user=user_with_person, district=district, level=DistrictUserRoleType.MANAGER)

        team = GroupSectionTeamFactory(section__group__district=district)

        section_id = to_base64("DistrictOrGroupSection", team.section.id)
        client = TestClient(self.url)
        with client.login(user_with_person):
            result = client.query(
                self.QUERY,
                variables={"sectionId": section_id},  # type: ignore[dict-item]
                assert_no_errors=False,
            )

        assert isinstance(result, Response)

        assert result.errors is None
        assert result.data == {
            "section": {
                "unitName": team.section.unit_name,
                "team": {
                    "displayName": team.display_name,
                    "teamType": {
                        "displayName": team.team_type.name,
                    },
                },
            }
        }

    def test_query__team_missing(self, user_with_person: User) -> None:
        district = DistrictFactory()
        DistrictUserRole.objects.create(user=user_with_person, district=district, level=DistrictUserRoleType.MANAGER)

        section = GroupSectionFactory(group__district=district)

        section_id = to_base64("DistrictOrGroupSection", section.id)
        client = TestClient(self.url)
        with client.login(user_with_person):
            result = client.query(
                self.QUERY,
                variables={"sectionId": section_id},  # type: ignore[dict-item]
                assert_no_errors=False,
            )

        assert isinstance(result, Response)

        assert result.errors == [
            {
                "locations": [{"column": 17, "line": 5}],
                "message": "Cannot return null for non-nullable field DistrictOrGroupSection.team.",
                "path": ["section", "team"],
            }
        ]
        assert result.data is None
