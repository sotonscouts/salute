from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class PersonDetail(BaseModel):
    id: UUID
    legal_name: str = Field(alias="firstname")
    preferred_name: str | None = Field(alias="preffered_name")
    last_name: str = Field(alias="lastname")
    membership_number: int = Field(alias="membershipno")
    primary_email: str | None = Field(alias="primaryEmail")
    default_email: str | None = Field(alias="defaultemail>>email")
    alternate_email: str | None = Field(alias="alternateemail>>email")
    is_suspended: bool = Field(alias="suspended")

    @field_validator("preferred_name", "primary_email", "default_email", "alternate_email", mode="after")
    @classmethod
    def normalise_empty_value(cls, val: str) -> str | None:
        return val or None
