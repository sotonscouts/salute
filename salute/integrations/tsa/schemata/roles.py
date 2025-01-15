from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class TeamMemberListingEntry(BaseModel):
    role_id: UUID = Field(alias="ContactMembershipId")

    # IDs for Unit and TeamType so we can find the team on our system.
    unit_id: UUID = Field(alias="unitid")
    team_id: UUID = Field(alias="TeamId")

    person_id: UUID = Field(alias="Id")  # Yes, the ID is the person, not the role.
    preferred_name: str = Field(alias="PreferredName")  # Not our typo. This is correct.
    last_name: str = Field(alias="Lastname")

    role_status: str | None = Field(alias="RoleStatusName")  # TODO: Can we get the ID for this?
    role_name: str = Field(alias="Role")  # TODO: Again, would be great if we can get the ID for this.

    @field_validator("role_name")
    @classmethod
    def fix_name_of_non_member(cls, val: str) -> str:
        if val == "Non Member - Needs dislosure":
            return "Non Member - Needs disclosure"
        return val


class TeamMemberListingResponse(BaseModel):
    data: list[TeamMemberListingEntry]
    next_page: int | None = Field(alias="nextPage")

    @field_validator("next_page", mode="before")
    @classmethod
    def normalise_empty_string(cls, val: str) -> int | None:
        if val:
            return int(val)
        return None
