from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class UnitAccreditationListingItem(BaseModel):
    id: UUID = Field(alias="MembershipId")
    accreditation_id: UUID = Field(alias="AccreditationId")
    accreditation_name: str = Field(alias="AccreditationName")
    person_id: UUID = Field(alias="HolderId")
    team_id: UUID = Field(alias="TeamId")
    unit_id: UUID = Field(alias="UnitId")
    status: str = Field(alias="Status")
    expires_at: datetime = Field(alias="ExpiryDate")
    granted_at: datetime = Field(alias="GrantedDate")


class UnitAccreditationListingResponse(BaseModel):
    data: list[UnitAccreditationListingItem]
    next_page: int | None = Field(alias="nextPage")

    @field_validator("next_page", mode="before")
    @classmethod
    def normalise_empty_string(cls, val: str) -> int | None:
        if val:
            return int(val)
        return None
