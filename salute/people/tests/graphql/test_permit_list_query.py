"""GraphQL root permit list fields on `PeopleQuery` (`salute.people.graphql.schema.PeopleQuery`)."""

from typing import Any
from zoneinfo import ZoneInfo

import pytest
from django.urls import reverse
from strawberry.relay import to_base64
from strawberry_django.test.client import Response, TestClient

from salute.accounts.models import DistrictUserRole, DistrictUserRoleType, User
from salute.hierarchy.factories import DistrictFactory
from salute.people.factories import (
    PermitActivityFactory,
    PermitCategoryFactory,
    PermitFactory,
    PermitStatusFactory,
    PermitTypeFactory,
    PersonFactory,
)
from salute.people.models import Permit


@pytest.mark.django_db
class TestPeopleQueryPermitListFields:
    url = reverse("graphql")

    PERMITS_QUERY = """
    query listPermits($filters: PermitFilter) {
        permits(filters: $filters) {
            totalCount
            edges {
                node {
                    person {
                        displayName
                    }
                    activity {
                        name
                    }
                    category {
                        name
                    }
                    type {
                        name
                    }
                    status {
                        name
                    }
                    startDate
                    dateOfPermitApplication
                    grantedOn
                    expiryDate
                    assessorName
                    restrictionDetails
                }
            }
        }
    }
    """

    TAXONOMY_QUERY = """
    query listPermitTaxonomies(
        $activityFilters: PermitActivityFilter
        $categoryFilters: PermitCategoryFilter
        $typeFilters: PermitTypeFilter
        $statusFilters: PermitStatusFilter
    ) {
        permitActivities(filters: $activityFilters) {
            totalCount
            edges {
                node {
                    name
                }
            }
        }
        permitCategories(filters: $categoryFilters) {
            totalCount
            edges {
                node {
                    name
                }
            }
        }
        permitTypes(filters: $typeFilters) {
            totalCount
            edges {
                node {
                    name
                }
            }
        }
        permitStatuses(filters: $statusFilters) {
            totalCount
            edges {
                node {
                    name
                }
            }
        }
    }
    """

    @staticmethod
    def _expected_permit_node(permit: Permit) -> dict[str, Any]:
        utc = ZoneInfo("UTC")
        return {
            "person": {"displayName": permit.person.display_name},
            "activity": {"name": permit.activity.name},
            "category": {"name": permit.category.name},
            "type": {"name": permit.type.name},
            "status": {"name": permit.status.name},
            "startDate": permit.start_date.isoformat(),
            "dateOfPermitApplication": permit.date_of_permit_application.astimezone(utc).isoformat(),
            "grantedOn": permit.granted_on.astimezone(utc).isoformat() if permit.granted_on else None,
            "expiryDate": permit.expiry_date.isoformat() if permit.expiry_date else None,
            "assessorName": permit.assessor_name,
            "restrictionDetails": permit.restriction_details,
        }

    @pytest.mark.parametrize(
        "field_name",
        [
            "permits",
            "permitActivities",
            "permitCategories",
            "permitTypes",
            "permitStatuses",
        ],
    )
    def test_query__not_authenticated(self, field_name: str) -> None:
        query = f"""
        query {{
            {field_name} {{
                totalCount
            }}
        }}
        """
        client = TestClient(self.url)
        results = client.query(query, assert_no_errors=False)

        assert isinstance(results, Response)
        assert results.data is None
        assert results.errors is not None
        assert len(results.errors) == 1
        assert results.errors[0]["message"] == "You don't have permission to list permits."
        assert results.errors[0]["path"] == [field_name]

    @pytest.mark.parametrize(
        "field_name",
        [
            "permits",
            "permitActivities",
            "permitCategories",
            "permitTypes",
            "permitStatuses",
        ],
    )
    def test_query__no_person(self, field_name: str, user: User) -> None:
        query = f"""
        query {{
            {field_name} {{
                totalCount
            }}
        }}
        """
        client = TestClient(self.url)
        with client.login(user):
            results = client.query(query, assert_no_errors=False)

        assert isinstance(results, Response)
        assert results.data is None
        assert results.errors is not None
        assert len(results.errors) == 1
        assert results.errors[0]["message"] == "You don't have permission to list permits."
        assert results.errors[0]["path"] == [field_name]

    def test_query__permits__user_sees_only_own(self, user_with_person: User) -> None:
        assert user_with_person.person is not None
        other_person = PersonFactory()
        PermitFactory.create_batch(size=2, person=other_person)
        own_permits = PermitFactory.create_batch(size=2, person=user_with_person.person)

        client = TestClient(self.url)
        with client.login(user_with_person):
            results = client.query(self.PERMITS_QUERY)

        assert isinstance(results, Response)
        sorted_own = sorted(
            own_permits,
            key=lambda p: (p.activity.name, p.category.name, p.type.name, p.status.name, p.start_date),
        )
        assert results.errors is None
        assert results.data == {
            "permits": {
                "totalCount": 2,
                "edges": [{"node": self._expected_permit_node(p)} for p in sorted_own],
            }
        }

    def test_query__permits__district_admin_sees_all(self, user_with_person: User) -> None:
        assert user_with_person.person is not None
        district = DistrictFactory()
        DistrictUserRole.objects.create(user=user_with_person, district=district, level=DistrictUserRoleType.ADMIN)

        other_person = PersonFactory()
        permits = [
            *PermitFactory.create_batch(size=2, person=other_person),
            *PermitFactory.create_batch(size=2, person=user_with_person.person),
        ]

        client = TestClient(self.url)
        with client.login(user_with_person):
            results = client.query(self.PERMITS_QUERY)

        assert isinstance(results, Response)
        sorted_permits = sorted(
            permits,
            key=lambda p: (p.activity.name, p.category.name, p.type.name, p.status.name, p.start_date),
        )
        assert results.errors is None
        assert results.data == {
            "permits": {
                "totalCount": 4,
                "edges": [{"node": self._expected_permit_node(p)} for p in sorted_permits],
            }
        }

    def test_query__permits__filter_by_activity(self, user_with_person: User) -> None:
        assert user_with_person.person is not None
        activity_keep = PermitActivityFactory(name="Keep Activity Unique")
        activity_other = PermitActivityFactory(name="Other Activity Unique")
        expected = PermitFactory(person=user_with_person.person, activity=activity_keep)
        PermitFactory(person=user_with_person.person, activity=activity_other)

        client = TestClient(self.url)
        with client.login(user_with_person):
            results = client.query(
                self.PERMITS_QUERY,
                variables={
                    "filters": {
                        "activity": {"name": {"exact": activity_keep.name}},
                    },
                },
            )

        assert isinstance(results, Response)
        assert results.errors is None
        assert results.data == {
            "permits": {
                "totalCount": 1,
                "edges": [{"node": self._expected_permit_node(expected)}],
            }
        }

    def test_query__permit_taxonomies__filtered_by_id(self, user_with_person: User) -> None:
        """Taxonomy lists are not scoped by person; `permit.list` is sufficient to query them."""
        assert user_with_person.person is not None
        activity_a = PermitActivityFactory(name="Taxonomy Alpha")
        activity_b = PermitActivityFactory(name="Taxonomy Beta")
        category_a = PermitCategoryFactory(name="Taxonomy Alpha")
        category_b = PermitCategoryFactory(name="Taxonomy Beta")
        type_a = PermitTypeFactory(name="Taxonomy Alpha")
        type_b = PermitTypeFactory(name="Taxonomy Beta")
        status_a = PermitStatusFactory(name="Taxonomy Alpha")
        status_b = PermitStatusFactory(name="Taxonomy Beta")

        client = TestClient(self.url)
        with client.login(user_with_person):
            results = client.query(
                self.TAXONOMY_QUERY,
                variables={
                    "activityFilters": {
                        "id": {
                            "inList": [
                                to_base64("PermitActivity", activity_a.id),
                                to_base64("PermitActivity", activity_b.id),
                            ],
                        },
                    },
                    "categoryFilters": {
                        "id": {
                            "inList": [
                                to_base64("PermitCategory", category_a.id),
                                to_base64("PermitCategory", category_b.id),
                            ],
                        },
                    },
                    "typeFilters": {
                        "id": {
                            "inList": [
                                to_base64("PermitType", type_a.id),
                                to_base64("PermitType", type_b.id),
                            ],
                        },
                    },
                    "statusFilters": {
                        "id": {
                            "inList": [
                                to_base64("PermitStatus", status_a.id),
                                to_base64("PermitStatus", status_b.id),
                            ],
                        },
                    },
                },
            )

        assert isinstance(results, Response)
        assert results.errors is None
        assert results.data == {
            "permitActivities": {
                "totalCount": 2,
                "edges": [{"node": {"name": name}} for name in sorted((activity_a.name, activity_b.name))],
            },
            "permitCategories": {
                "totalCount": 2,
                "edges": [{"node": {"name": name}} for name in sorted((category_a.name, category_b.name))],
            },
            "permitTypes": {
                "totalCount": 2,
                "edges": [{"node": {"name": name}} for name in sorted((type_a.name, type_b.name))],
            },
            "permitStatuses": {
                "totalCount": 2,
                "edges": [{"node": {"name": name}} for name in sorted((status_a.name, status_b.name))],
            },
        }
