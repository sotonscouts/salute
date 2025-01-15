from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class RoleInfo(BaseModel):
    role_id: UUID = Field(alias="id")
    name: str


class TeamsAndRolesListingTeamEntry(BaseModel):
    team_id: UUID = Field(alias="teamId")
    team_name: str = Field(alias="teamName")
    parent_team_id: UUID | None = Field(alias="parentTeamId")
    allow_sub_team: bool = Field(alias="allowSubTeam")
    inherit_permissions: bool = Field(alias="inheritPermissions")

    roles: list[RoleInfo]

    @field_validator("parent_team_id", mode="before")
    @classmethod
    def normalise_null(cls, val: str) -> str | None:
        return val or None


class TeamsAndRolesListingResponse(BaseModel):
    teams: list[TeamsAndRolesListingTeamEntry]
