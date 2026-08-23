from unittest import mock

import pytest
from django.urls import reverse
from strawberry_django.test.client import Response, TestClient

from salute.accounts.models import User
from salute.api.auth0.auth import AuthInfo
from salute.api.scopes import ApiScope
from salute.hierarchy.factories import DistrictFactory, GroupFactory, GroupSectionFactory


@pytest.mark.django_db
class TestHierarchyServiceAccountAccess:
    url = reverse("graphql")

    @staticmethod
    def _query(
        query: str,
        user: User,
        scopes: list[ApiScope | str],
        *,
        variables: dict[str, object] | None = None,
        assert_no_errors: bool = True,
    ) -> Response:
        with mock.patch(
            "salute.api.views.authenticate_user_with_bearer_token",
            return_value=AuthInfo(user=user, scopes=list(scopes)),
        ):
            client = TestClient(TestHierarchyServiceAccountAccess.url)
            result = client.query(
                query,
                variables=variables,
                headers={"Authorization": "Bearer token"},
                assert_no_errors=assert_no_errors,
            )
        assert isinstance(result, Response)
        return result

    def test_district__with_hierarchy_read(self, user_with_service_account: User) -> None:
        district = DistrictFactory()
        group = GroupFactory(district=district)

        result = self._query(
            """
            query {
                district {
                    unitName
                    shortcode
                    groups {
                        edges {
                            node {
                                unitName
                            }
                        }
                        totalCount
                    }
                }
            }
            """,
            user_with_service_account,
            [ApiScope.HIERARCHY_READ],
        )

        assert result.errors is None
        assert result.data == {
            "district": {
                "unitName": district.unit_name,
                "shortcode": district.shortcode,
                "groups": {
                    "edges": [{"node": {"unitName": group.unit_name}}],
                    "totalCount": 1,
                },
            }
        }

    def test_groups__with_hierarchy_read(self, user_with_service_account: User) -> None:
        group = GroupFactory()

        result = self._query(
            """
            query {
                groups {
                    edges {
                        node {
                            unitName
                            district {
                                unitName
                            }
                        }
                    }
                    totalCount
                }
            }
            """,
            user_with_service_account,
            [ApiScope.HIERARCHY_READ],
        )

        assert result.errors is None
        assert result.data == {
            "groups": {
                "edges": [
                    {
                        "node": {
                            "unitName": group.unit_name,
                            "district": {"unitName": group.district.unit_name},
                        }
                    }
                ],
                "totalCount": 1,
            }
        }

    def test_sections__with_hierarchy_read(self, user_with_service_account: User) -> None:
        section = GroupSectionFactory()

        result = self._query(
            """
            query {
                sections {
                    edges {
                        node {
                            unitName
                            group {
                                unitName
                            }
                        }
                    }
                    totalCount
                }
            }
            """,
            user_with_service_account,
            [ApiScope.HIERARCHY_READ],
        )

        assert result.errors is None
        assert result.data == {
            "sections": {
                "edges": [
                    {
                        "node": {
                            "unitName": section.unit_name,
                            "group": {"unitName": section.group.unit_name},
                        }
                    }
                ],
                "totalCount": 1,
            }
        }

    def test_section_types__with_hierarchy_read(self, user_with_service_account: User) -> None:
        result = self._query(
            """
            query {
                sectionTypes {
                    value
                    displayName
                }
            }
            """,
            user_with_service_account,
            [ApiScope.HIERARCHY_READ],
        )

        assert result.errors is None
        assert result.data is not None
        assert [item["value"] for item in result.data["sectionTypes"]] == [
            "SQUIRRELS",
            "BEAVERS",
            "CUBS",
            "SCOUTS",
            "EXPLORERS",
            "YOUNG_LEADERS",
            "NETWORK",
        ]

    @pytest.mark.parametrize(
        ("query", "path", "message"),
        [
            pytest.param(
                "query { district { unitName } }",
                ["district"],
                "You don't have permission to view the district.",
                id="district",
            ),
            pytest.param(
                "query { groups { totalCount } }",
                ["groups"],
                "You don't have permission to list groups.",
                id="groups",
            ),
            pytest.param(
                "query { sections { totalCount } }",
                ["sections"],
                "You don't have permission to list sections.",
                id="sections",
            ),
            pytest.param(
                "query { sectionTypes { value } }",
                ["sectionTypes"],
                "You don't have permission to list section types.",
                id="section-types",
            ),
        ],
    )
    @pytest.mark.parametrize(
        "scopes",
        [
            pytest.param([], id="no-scopes"),
            pytest.param([ApiScope.WIFI_ACCOUNTS_READ], id="wrong-scope"),
        ],
    )
    def test_denied_without_hierarchy_read(
        self,
        user_with_service_account: User,
        query: str,
        path: list[str],
        message: str,
        scopes: list[ApiScope],
    ) -> None:
        DistrictFactory()
        result = self._query(query, user_with_service_account, scopes, assert_no_errors=False)

        assert result.data is None
        assert result.errors == [
            {
                "message": message,
                "locations": [{"line": 1, "column": 9}],
                "path": path,
            }
        ]

    def test_privileged_fields_remain_hidden(self, user_with_service_account: User) -> None:
        DistrictFactory()
        result = self._query(
            """
            query {
                district {
                    youngPersonCount
                    teams {
                        displayName
                    }
                }
            }
            """,
            user_with_service_account,
            [ApiScope.HIERARCHY_READ],
        )

        assert result.errors is None
        assert result.data == {
            "district": {
                "youngPersonCount": None,
                "teams": [],
            }
        }
