from datetime import date, datetime
from enum import IntEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class UnitTypeID(IntEnum):
    GROUP = 866060001
    GROUP_SECTION = 866060000
    DISTRICT_SECTION = 866060002


class UnitListingResult(BaseModel):
    """
    A result from UnitListingAsync.

    We do not need all fields, so we do not parse them.
    """

    id: UUID
    unit_name: str = Field(alias="unitName")
    unit_shortcode: str = Field(alias="unitShortCode")
    unit_type: str = Field(alias="unitType")
    unit_type_id: int = Field(alias="unitTypeId")


class UnitListingPageResult(BaseModel):
    data: list[UnitListingResult]
    nexttoken: str | None  # int as string, starting from zero, or ""

    @field_validator("nexttoken", mode="after")
    @classmethod
    def parse_empty_string_to_none(cls, val: str) -> str | None:
        return None if val == "" else val


class UnitDetailAdminDetails(BaseModel):
    date_of_creation: date | None = Field(alias="dateOfCreation")
    last_modified: datetime | None = Field(alias="modificationDate")
    unit_shortcode: str = Field(alias="uniqueId")

    @field_validator("date_of_creation", mode="before")
    @classmethod
    def remove_time_from_iso8601(cls, val: str | None) -> str | None:
        if not val:
            return None
        return val[:10]


class UnitDetail(BaseModel):
    id: UUID
    section_type: str | None = Field(alias="sectionType", default=None)
    level_type: str | None = Field(alias="levelType")
    name: str
    charity_number: int | None = Field(alias="registeredCharityNumber")
    parent_unit_id: UUID = Field(alias="parentUnitId")
    admin_details: UnitDetailAdminDetails = Field(alias="adminDetails")

    @field_validator("charity_number", "section_type", "level_type", mode="before")
    @classmethod
    def normalise_nullables(cls, val: Any) -> Any:
        return val or None
