from collections.abc import Iterator

from pydantic import BaseModel, Field


class OSMSection(BaseModel):
    """Schema for a section in the OSM API response."""

    section_id: str = Field(alias="sectionid")
    name: str = Field(alias="name")
    young_person_count: int = Field(alias="numscouts")
    adult_count: int | None = Field(alias="numleaders")


class OSMGroup(BaseModel):
    """Schema for a group in the OSM API response."""

    sections: list[OSMSection]


class OSMDistrict(BaseModel):
    """Schema for a district in the OSM API response."""

    by_group: dict[str, OSMGroup] = Field(alias="byGroup")


class OSMCountsResponse(BaseModel):
    """Schema for the OSM API response for section counts."""

    districts: dict[str, OSMDistrict]

    def iter_sections(self) -> Iterator[OSMSection]:
        """Iterate over all sections in the response."""
        for district in self.districts.values():
            for group in district.by_group.values():
                yield from group.sections

    @classmethod
    def model_validate_api_response(cls, data: dict) -> "OSMCountsResponse":
        """Validate and parse the raw API response into a structured model."""
        # Filter out any non-district keys (like 'categories')
        districts = {k: v for k, v in data.items() if k != "categories"}
        return cls(districts=districts)
