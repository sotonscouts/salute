from uuid import UUID

from salute.integrations.tsa.schemata.units import UnitListingPageResult, UnitListingResult


class TestUnitListingResultSchema:
    example_data = {
        "id": "00000000-0000-0000-0000-000000000001",
        "contactPerson": " ",
        "contactAddress": "Jane Smith\r\n123 Example Lane\r\nExampleton, Exampleshire AB12 3CD\r\nUnited Kingdom",
        "contactEmail": "jane.smith@example.org.uk",
        "parentUnit": "1st Example Scout Group",
        "parentUnitId": "00000000-0000-0000-0000-000000000002",
        "unitName": "1st Example Scout Group - Beaver Scout 1",
        "unitType": "Group Section",
        "unitTypeId": "866060000",
        "unitPrefix": "S10000000>>S10000000>>S10000000>>S10000000>>S10000000>>S10000000",
        "countryId": "00000000-0000-0000-0000-000000000003",
        "unitShortCode": "S10000000",
        "regionId": "00000000-0000-0000-0000-000000000004",
        "countyId": "00000000-0000-0000-0000-000000000005",
        "districtId": "00000000-0000-0000-0000-000000000006",
        "groupId": "00000000-0000-0000-0000-000000000007",
        "groupSectionId": "",
        "districtSectionId": "",
        "countySectionId": "",
        "IMD": "",
        "IMDIndex": "",
        "UnitLevel": 1,
    }

    def test_parse_item(self) -> None:
        unit = UnitListingResult.model_validate(self.example_data)
        assert unit.id == UUID("00000000-0000-0000-0000-000000000001")
        assert unit.unit_name == "1st Example Scout Group - Beaver Scout 1"
        assert unit.unit_shortcode == "S10000000"

    def test_parse_page(self) -> None:
        page = UnitListingPageResult.model_validate(
            {
                "data": [self.example_data, self.example_data],
                "nexttoken": "1",
            }
        )
        assert len(page.data) == 2
        assert page.nexttoken == "1"

    def test_parse_page__last_page(self) -> None:
        page = UnitListingPageResult.model_validate(
            {
                "data": [],
                "nexttoken": "",
            }
        )
        assert len(page.data) == 0
        assert page.nexttoken is None
