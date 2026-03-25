from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class ContactFields(BaseModel):
    """Custom fields for an Email Octopus contact."""

    first_name: str | None = Field(None, alias="FirstName")
    last_name: str | None = Field(None, alias="LastName")
    membership_number: str | None = Field(None, alias="MembershipNumber")
    is_member: str | None = Field(None, alias="IsMember")
    salute_id: str | None = Field(None, alias="SaluteId")
    tsa_id: str | None = Field(None, alias="TSAId")

    class Config:
        populate_by_name = True


ContactStatus = Literal["pending", "subscribed", "unsubscribed"]


class UpdateContactItem(BaseModel):
    """Schema for a single contact in a bulk update request."""

    id: str
    email_address: str | None = None
    fields: dict[str, str] | None = None
    tags: dict[str, bool] | None = None
    status: ContactStatus | None = None


class BulkUpdateContactsRequest(BaseModel):
    """Schema for bulk updating contacts."""

    contacts: list[UpdateContactItem]


class Contact(BaseModel):
    """Schema for an Email Octopus contact."""

    id: str
    email_address: str
    fields: ContactFields
    tags: list[str]
    status: ContactStatus
    created_at: datetime
    last_updated_at: datetime | None = None


class ContactsResponse(BaseModel):
    """Schema for the Email Octopus contacts list response."""

    data: list[Contact]
    paging: dict[str, Any]


class CreateContactRequest(BaseModel):
    """Schema for creating a new Email Octopus contact."""

    email_address: str
    fields: dict[str, str] | None = None
    tags: list[str] | None = None
    status: ContactStatus | None = None
