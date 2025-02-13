from uuid import UUID

import pytest
from django.urls import reverse
from strawberry.relay import to_base64
from strawberry_django.test.client import Response, TestClient

from salute.accounts.models import User
from salute.hierarchy.constants import SectionType
from salute.hierarchy.factories import DistrictSectionFactory, GroupSectionFactory


@pytest.mark.django_db
class TestSectionQuery:
    url = reverse("graphql")

    QUERY = """
        query getSection($sectionId: GlobalID!) {
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
            {"message": "User is not authenticated.", "locations": [{"line": 3, "column": 9}], "path": ["section"]}
        ]
        assert results.data is None

    def test_query__no_section(self, admin_user: User) -> None:
        section_id = to_base64("Section", UUID(int=0))
        client = TestClient(self.url)
        with client.login(admin_user):
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

    def test_query__group_section(self, admin_user: User) -> None:
        section = GroupSectionFactory()
        section_id = to_base64("DistrictOrGroupSection", section.id)
        client = TestClient(self.url)
        with client.login(admin_user):
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

    def test_query__district_section(self, admin_user: User) -> None:
        section = DistrictSectionFactory()
        section_id = to_base64("DistrictOrGroupSection", section.id)
        client = TestClient(self.url)
        with client.login(admin_user):
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


class TestSectionTypeInfoQuery:
    url = reverse("graphql")

    QUERY = """
        query getSection($sectionId: GlobalID!) {
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

    def test_query__group_section(self, admin_user: User) -> None:
        section = GroupSectionFactory(section_type=SectionType.BEAVERS)
        section_id = to_base64("DistrictOrGroupSection", section.id)
        client = TestClient(self.url)
        with client.login(admin_user):
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

    def test_query__district_section(self, admin_user: User) -> None:
        section = DistrictSectionFactory(section_type=SectionType.EXPLORERS)
        section_id = to_base64("DistrictOrGroupSection", section.id)
        client = TestClient(self.url)
        with client.login(admin_user):
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
