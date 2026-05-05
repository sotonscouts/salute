from datetime import datetime
from uuid import UUID
from zoneinfo import ZoneInfo

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


class PermitDetail(BaseModel):
    membership_number: int = Field(alias="Membership number")
    permit_activity: str = Field(alias="Permit activity")
    permit_category: str = Field(alias="Permit category")
    permit_type: str = Field(alias="Permit Type")
    expiry_date: datetime | None = Field(alias="Expiry date")
    status: str = Field(alias="Status")
    permit_restriction_details: str = Field(alias="Permit restriction details")
    start_date: datetime = Field(alias="Start date")
    assessor_name: str = Field(alias="Assessor name")
    date_of_permit_application: datetime = Field(alias="Date of permit application")
    granted_on: datetime | None = Field(alias="Granted on")

    @field_validator("assessor_name", mode="before")
    @classmethod
    def normalise_empty_string(cls, val: str) -> str:
        return val or ""

    @field_validator("expiry_date", "start_date", "date_of_permit_application", "granted_on", mode="after")
    @classmethod
    def normalise_datetime(cls, val: datetime | None) -> datetime | None:
        if val:
            return val.replace(tzinfo=ZoneInfo("Europe/London"))
        return None


class PermitListingResponse(BaseModel):
    data: list[PermitDetail]
    next_page: int | None = Field(alias="nextPage")

    @field_validator("next_page", mode="before")
    @classmethod
    def normalise_empty_string(cls, val: str) -> int | None:
        if val:
            return int(val)
        return None
