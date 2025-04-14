from datetime import datetime

from pydantic import BaseModel, Field


class NameInfo(BaseModel):
    given_name: str = Field(alias="givenName")
    family_name: str = Field(alias="familyName")
    full_name: str = Field(alias="fullName")


class ExternalIdInfo(BaseModel):
    value: str
    type: str | None


class WorkspaceAccountInfo(BaseModel):
    id: int
    primary_email: str = Field(alias="primaryEmail")
    name: NameInfo
    is_admin: bool = Field(alias="isAdmin")
    is_delegated_admin: bool = Field(alias="isDelegatedAdmin")
    last_login_time: datetime | None = Field(alias="lastLoginTime")
    creation_time: datetime = Field(alias="creationTime")
    agreed_to_terms: bool = Field(alias="agreedToTerms")
    suspended: bool
    archived: bool
    change_password_at_next_login: bool = Field(alias="changePasswordAtNextLogin")
    external_ids: list[ExternalIdInfo] | None = Field(alias="externalIds", default=None)
    org_unit_path: str | None = Field(alias="orgUnitPath")
    is_mailbox_setup: bool = Field(alias="isMailboxSetup")
    is_enrolled_in_2sv: bool = Field(alias="isEnrolledIn2Sv")
    is_enforced_in_2sv: bool = Field(alias="isEnforcedIn2Sv")
    include_in_global_address_list: bool = Field(alias="includeInGlobalAddressList")
    recovery_email: str | None = Field(alias="recoveryEmail", default=None)
    recovery_phone: str | None = Field(alias="recoveryPhone", default=None)
    aliases: list[str] = Field(default=[])


class WorkspaceGroupInfo(BaseModel):
    id: str
    email: str
    name: str
    description: str = ""
    aliases: list[str] = []
