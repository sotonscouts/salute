from typing import Any
from uuid import UUID

import pytest
from django.urls import reverse
from strawberry.relay import to_base64
from strawberry_django.test.client import Response, TestClient

from salute.accounts.models import DistrictUserRole, DistrictUserRoleType, User
from salute.hierarchy.factories import DistrictFactory, DistrictSectionFactory, GroupFactory, GroupSectionFactory
from salute.locations.constants import TenureType
from salute.locations.factories import (
    DistrictSiteOperatorFactory,
    GroupSiteOperatorFactory,
    SiteFactory,
    ThirdPartySiteOperatorFactory,
)


@pytest.mark.django_db
class TestSiteQuery:
    url = reverse("graphql")

    QUERY = """
    query getSite($siteId: ID!) {
        site(siteId: $siteId) {
            id
            displayName
            operator {
                displayName
            }
            tenureType
            uprn
            buildingName
            streetNumber
            street
            town
            county
            postcode
            location {
                latitude
                longitude
            }
        }
    }
    """

    def test_query__not_authenticated(self) -> None:
        site = SiteFactory()
        site_id = to_base64("Site", site.id)
        client = TestClient(self.url)
        results = client.query(
            self.QUERY,
            variables={"siteId": site_id},  # type: ignore[dict-item]
            assert_no_errors=False,
        )

        assert isinstance(results, Response)

        assert results.errors == [
            {
                "message": "You don't have permission to view that site.",
                "locations": [{"line": 3, "column": 9}],
                "path": ["site"],
            }
        ]
        assert results.data is None

    def test_query__no_permission(self, user: User) -> None:
        site = SiteFactory()
        site_id = to_base64("Site", site.id)
        client = TestClient(self.url)
        with client.login(user):
            results = client.query(
                self.QUERY,
                variables={"siteId": site_id},  # type: ignore[dict-item]
                assert_no_errors=False,
            )

        assert isinstance(results, Response)

        assert results.errors == [
            {
                "message": "You don't have permission to view that site.",
                "locations": [{"line": 3, "column": 9}],
                "path": ["site"],
            }
        ]
        assert results.data is None

    def test_query__no_site(self, user_with_person: User) -> None:
        """This should not happen in production. There must always be exactly one district."""
        site_id = to_base64("Site", UUID(int=0))
        client = TestClient(self.url)
        with client.login(user_with_person):
            result = client.query(
                self.QUERY,
                variables={"siteId": site_id},  # type: ignore[dict-item]
                assert_no_errors=False,
            )

        assert isinstance(result, Response)

        assert result.data is None
        assert result.errors == [
            {
                "locations": [{"column": 9, "line": 3}],
                "message": "Site matching query does not exist.",
                "path": ["site"],
            }
        ]

    def test_query__admin(self, user_with_person: User) -> None:
        district = DistrictFactory()
        DistrictUserRole.objects.create(user=user_with_person, district=district, level=DistrictUserRoleType.ADMIN)
        site = SiteFactory()
        site_id = to_base64("Site", site.id)
        client = TestClient(self.url)
        with client.login(user_with_person):
            result = client.query(
                self.QUERY,
                variables={"siteId": site_id},  # type: ignore[dict-item]
                assert_no_errors=False,
            )

        assert isinstance(result, Response)

        assert result.data == {
            "site": {
                "id": site_id,
                "displayName": site.name,
                "operator": {
                    "displayName": site.operator.display_name,
                },
                "tenureType": TenureType(site.tenure_type).name,
                "uprn": site.uprn,
                "buildingName": site.building_name,
                "streetNumber": site.street_number,
                "street": site.street,
                "town": site.town,
                "county": site.county,
                "postcode": site.postcode,
                "location": {
                    "latitude": round(float(site.latitude), 6),
                    "longitude": round(float(site.longitude), 6),
                },
            }
        }

    def test_query__manager(self, user_with_person: User) -> None:
        district = DistrictFactory()
        DistrictUserRole.objects.create(user=user_with_person, district=district, level=DistrictUserRoleType.MANAGER)
        site = SiteFactory()
        site_id = to_base64("Site", site.id)
        client = TestClient(self.url)
        with client.login(user_with_person):
            result = client.query(
                self.QUERY,
                variables={"siteId": site_id},  # type: ignore[dict-item]
            )

        assert isinstance(result, Response)

        assert result.data["site"]["tenureType"] == TenureType(site.tenure_type).name  # type: ignore[index]

    def test_query__unprivileged(self, user_with_person: User) -> None:
        site = SiteFactory()
        site_id = to_base64("Site", site.id)
        client = TestClient(self.url)
        with client.login(user_with_person):
            result = client.query(
                self.QUERY,
                variables={"siteId": site_id},  # type: ignore[dict-item]
            )

        assert isinstance(result, Response)

        assert result.data["site"]["tenureType"] is None  # type: ignore[index]


@pytest.mark.django_db
class TestSiteJoinOperatorQuery:
    url = reverse("graphql")

    QUERY = """
    query getSiteWithOperator($siteId: ID!) {
        site(siteId: $siteId) {
            id
            displayName
            operator {
                displayName
                district {
                    displayName
                }
                group {
                    displayName
                }
            }
        }
    }
    """

    def test_query__third_party(self, user_with_person: User) -> None:
        operator = ThirdPartySiteOperatorFactory()
        site = SiteFactory(operator=operator)
        site_id = to_base64("Site", site.id)
        client = TestClient(self.url)
        with client.login(user_with_person):
            result = client.query(
                self.QUERY,
                variables={"siteId": site_id},  # type: ignore[dict-item]
            )

        assert isinstance(result, Response)

        assert result.data == {
            "site": {
                "id": site_id,
                "displayName": site.name,
                "operator": {
                    "displayName": operator.name,
                    "district": None,
                    "group": None,
                },
            }
        }

    def test_query__district(self, user_with_person: User) -> None:
        district = DistrictFactory()
        operator = DistrictSiteOperatorFactory(district=district)
        site = SiteFactory(operator=operator)
        site_id = to_base64("Site", site.id)
        client = TestClient(self.url)
        with client.login(user_with_person):
            result = client.query(
                self.QUERY,
                variables={"siteId": site_id},  # type: ignore[dict-item]
            )

        assert isinstance(result, Response)

        assert result.data == {
            "site": {
                "id": site_id,
                "displayName": site.name,
                "operator": {
                    "displayName": district.unit_name,
                    "district": {
                        "displayName": district.unit_name,
                    },
                    "group": None,
                },
            }
        }

    def test_query__group(self, user_with_person: User) -> None:
        group = GroupFactory()
        operator = GroupSiteOperatorFactory(group=group)
        site = SiteFactory(operator=operator)
        site_id = to_base64("Site", site.id)
        client = TestClient(self.url)
        with client.login(user_with_person):
            result = client.query(
                self.QUERY,
                variables={"siteId": site_id},  # type: ignore[dict-item]
            )

        assert isinstance(result, Response)

        assert result.data == {
            "site": {
                "id": site_id,
                "displayName": site.name,
                "operator": {
                    "displayName": group.display_name,
                    "district": None,
                    "group": {
                        "displayName": group.display_name,
                    },
                },
            }
        }


@pytest.mark.django_db
class TestSiteJoinGroupsQuery:
    url = reverse("graphql")

    QUERY = """
    query getSiteWithGroups($siteId: ID!) {
        site(siteId: $siteId) {
            id
            displayName
            groups {
                edges {
                    node {
                        displayName
                    }
                }
            }
        }
    }
    """

    def test_query__no_groups(self, user_with_person: User) -> None:
        site = SiteFactory()
        site_id = to_base64("Site", site.id)
        client = TestClient(self.url)
        with client.login(user_with_person):
            result = client.query(
                self.QUERY,
                variables={"siteId": site_id},  # type: ignore[dict-item]
            )

        assert isinstance(result, Response)

        assert result.data == {
            "site": {
                "id": site_id,
                "displayName": site.name,
                "groups": {
                    "edges": [],
                },
            }
        }

    def test_query__with_groups(self, user_with_person: User) -> None:
        site = SiteFactory()
        group = GroupFactory(primary_site=site)
        site_id = to_base64("Site", site.id)
        client = TestClient(self.url)
        with client.login(user_with_person):
            result = client.query(
                self.QUERY,
                variables={"siteId": site_id},  # type: ignore[dict-item]
            )

        assert isinstance(result, Response)

        assert result.data == {
            "site": {
                "id": site_id,
                "displayName": site.name,
                "groups": {
                    "edges": [
                        {
                            "node": {
                                "displayName": group.display_name,
                            },
                        },
                    ],
                },
            }
        }


@pytest.mark.django_db
class TestSiteJoinSectionsQuery:
    url = reverse("graphql")

    QUERY = """
    query getSiteWithSections($siteId: ID!, $explicitOnly: Boolean) {
        site(siteId: $siteId) {
            id
            displayName
            sections(explicitOnly: $explicitOnly) {
                edges {
                    node {
                        displayName
                    }
                }
            }
        }
    }
    """

    def test_query__no_sections(self, user_with_person: User) -> None:
        site = SiteFactory()
        site_id = to_base64("Site", site.id)
        client = TestClient(self.url)
        with client.login(user_with_person):
            result = client.query(
                self.QUERY,
                variables={"siteId": site_id},  # type: ignore[dict-item]
            )

        assert isinstance(result, Response)

        assert result.data == {
            "site": {
                "id": site_id,
                "displayName": site.name,
                "sections": {
                    "edges": [],
                },
            }
        }

    @pytest.mark.parametrize("explicit_only", [True, None, False])
    def test_query__explicit_only(self, user_with_person: User, *, explicit_only: bool | None) -> None:
        site = SiteFactory()
        district_section = DistrictSectionFactory(site=site)
        explicit_group_section = GroupSectionFactory(site=site)
        implicit_group_section = GroupSectionFactory(group__primary_site=site)
        site_id = to_base64("Site", site.id)

        expected_sections = [district_section, explicit_group_section]
        if explicit_only is not True:
            expected_sections.append(implicit_group_section)

        client = TestClient(self.url)

        variables: dict[str, Any] = {"siteId": site_id}
        if explicit_only is not None:
            variables["explicitOnly"] = explicit_only

        with client.login(user_with_person):
            result = client.query(self.QUERY, variables=variables)

        assert isinstance(result, Response)

        returned_sections = {section["node"]["displayName"] for section in result.data["site"]["sections"]["edges"]}  # type: ignore

        assert returned_sections == {section.display_name for section in expected_sections}
