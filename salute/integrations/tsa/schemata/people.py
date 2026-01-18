from uuid import UUID

import phonenumbers
from django.conf import settings
from pydantic import BaseModel, Field, field_validator


class PersonDetail(BaseModel):
    id: UUID
    legal_name: str = Field(alias="firstname")
    preferred_name: str | None = Field(alias="preffered_name")
    last_name: str = Field(alias="lastname")
    membership_number: int = Field(alias="membershipno")
    default_email: str | None = Field(alias="defaultemail>>email")
    alternate_email: str | None = Field(alias="alternateemail>>email")
    is_suspended: bool = Field(alias="suspended")
    phone_number: str | None = Field(alias="defaultphone>>phone")
    alternate_phone_number: str | None = Field(alias="alternatephone>>phone")

    @field_validator("preferred_name", "default_email", "alternate_email", mode="after")
    @classmethod
    def normalise_empty_value(cls, val: str) -> str:
        return val or ""

    @field_validator("phone_number", "alternate_phone_number", mode="after")
    @classmethod
    def normalise_phone_number(cls, val: str) -> str | None:
        if val:
            try:
                phone_number = phonenumbers.parse(val, region=settings.PHONENUMBER_DEFAULT_REGION)  # type: ignore[misc]
                if phonenumbers.is_valid_number(phone_number):
                    return val
            except phonenumbers.phonenumberutil.NumberParseException:
                return None
        return None
