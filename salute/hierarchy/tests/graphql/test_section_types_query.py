from django.urls import reverse
from strawberry_django.test.client import Response, TestClient

from salute.accounts.models import User


class TestGetSectionTypesQuery:
    url = reverse("graphql")

    GET_SECTION_TYPES_QUERY = """
    query {
        sectionTypes {
            value
            displayName
            operatingCategory
            formattedAgeRange
        }
    }
    """

    def test_get_section_types_query__not_authenticated(self) -> None:
        client = TestClient(self.url)
        results = client.query(self.GET_SECTION_TYPES_QUERY, assert_no_errors=False)

        assert isinstance(results, Response)

        assert results.errors == [
            {"message": "User is not authenticated.", "locations": [{"line": 3, "column": 9}], "path": ["sectionTypes"]}
        ]
        assert results.data is None

    def test_get_section_types_query__cannot_query_private_fields(self, admin_user: User) -> None:
        client = TestClient(self.url)
        with client.login(admin_user):
            results = client.query(
                """
                query {
                    sectionTypes {
                        value
                        maxAge
                        minAge
                    }
                }
            """,
                assert_no_errors=False,
            )

        assert isinstance(results, Response)

        assert results.errors == [
            {
                "message": "Cannot query field 'maxAge' on type 'SectionTypeInfo'.",
                "locations": [{"line": 5, "column": 25}],
            },
            {
                "locations": [{"column": 25, "line": 6}],
                "message": "Cannot query field 'minAge' on type 'SectionTypeInfo'.",
            },
        ]
        assert results.data is None

    def test_get_section_types_query__authenticated(self, admin_user: User) -> None:
        client = TestClient(self.url)
        with client.login(admin_user):
            result = client.query(self.GET_SECTION_TYPES_QUERY)

        assert isinstance(result, Response)

        assert result.errors is None
        assert result.data == {
            "sectionTypes": [
                {
                    "value": "SQUIRRELS",
                    "displayName": "Squirrels",
                    "operatingCategory": "GROUP",
                    "formattedAgeRange": "4 - 5 years",
                },
                {
                    "value": "BEAVERS",
                    "displayName": "Beavers",
                    "operatingCategory": "GROUP",
                    "formattedAgeRange": "6 - 8 years",
                },
                {
                    "value": "CUBS",
                    "displayName": "Cubs",
                    "operatingCategory": "GROUP",
                    "formattedAgeRange": "8 - 10½ years",
                },
                {
                    "value": "SCOUTS",
                    "displayName": "Scouts",
                    "operatingCategory": "GROUP",
                    "formattedAgeRange": "10½ - 14 years",
                },
                {
                    "value": "EXPLORERS",
                    "displayName": "Explorers",
                    "operatingCategory": "DISTRICT",
                    "formattedAgeRange": "14 - 18 years",
                },
                {
                    "value": "YOUNG_LEADERS",
                    "displayName": "Young Leaders",
                    "operatingCategory": "DISTRICT",
                    "formattedAgeRange": "14 - 18 years",
                },
                {
                    "value": "NETWORK",
                    "displayName": "Network",
                    "operatingCategory": "DISTRICT",
                    "formattedAgeRange": "18 - 25 years",
                },
            ]
        }
