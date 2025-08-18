import pytest
from pydantic import ValidationError

from salute.integrations.osm.schemata import OSMCountsResponse, OSMSection


def test_osm_section_validation() -> None:
    """Test that OSMSection validates correctly."""
    # Test valid data
    section = OSMSection.model_validate(
        {
            "sectionid": "123",
            "name": "Test Section",
            "numscouts": 10,
            "numleaders": 2,
        }
    )
    assert section.section_id == "123"
    assert section.name == "Test Section"
    assert section.young_person_count == 10
    assert section.adult_count == 2

    # Test missing optional field
    section = OSMSection.model_validate(
        {
            "sectionid": "123",
            "name": "Test Section",
            "numscouts": 10,
            "numleaders": None,
        }
    )
    assert section.adult_count is None

    # Test invalid data
    with pytest.raises(ValidationError):
        OSMSection.model_validate(
            {
                "sectionid": "123",
                "name": "Test Section",
                "numscouts": "not a number",
            }
        )


def test_osm_counts_response_validation() -> None:
    """Test that OSMCountsResponse validates correctly."""
    # Test valid data
    data = {
        "district1": {
            "byGroup": {
                "group1": {
                    "sections": [
                        {
                            "sectionid": "123",
                            "name": "Test Section",
                            "numscouts": 10,
                            "numleaders": 2,
                        }
                    ]
                }
            }
        },
        "categories": ["some", "categories"],
    }
    response = OSMCountsResponse.model_validate_api_response(data)
    assert len(response.districts) == 1
    assert "district1" in response.districts
    assert len(response.districts["district1"].by_group) == 1
    assert "group1" in response.districts["district1"].by_group
    assert len(response.districts["district1"].by_group["group1"].sections) == 1
    section = response.districts["district1"].by_group["group1"].sections[0]
    assert section.section_id == "123"
    assert section.name == "Test Section"
    assert section.young_person_count == 10
    assert section.adult_count == 2

    # Test that categories are filtered out
    assert "categories" not in response.districts

    # Test iter_sections
    sections = list(response.iter_sections())
    assert len(sections) == 1
    assert sections[0].section_id == "123"
    assert sections[0].name == "Test Section"

    # Test invalid data
    with pytest.raises(ValidationError):
        OSMCountsResponse.model_validate_api_response(
            {
                "district1": {
                    "byGroup": {
                        "group1": {
                            "sections": [
                                {
                                    "sectionid": "123",
                                    "name": "Test Section",
                                    "numscouts": "not a number",
                                }
                            ]
                        }
                    }
                }
            }
        )
