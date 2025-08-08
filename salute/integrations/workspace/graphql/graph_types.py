from __future__ import annotations

import zoneinfo
from datetime import datetime
from typing import TYPE_CHECKING, Annotated

import strawberry as sb
import strawberry_django as sd
from strawberry_django.permissions import HasSourcePerm

from salute.integrations.workspace import models

if TYPE_CHECKING:
    from salute.people.graphql.graph_types import Person


@sd.type(models.WorkspaceAccount)
class WorkspaceAccount(sb.relay.Node):
    person: Annotated[Person, sb.lazy("salute.people.graphql.graph_types")] | None = sd.field(
        description="Person associated with the user"
    )  # noqa: E501
    google_id: str = sb.field(description="Google ID")
    primary_email: str = sb.field(description="Primary Email")

    # Editable Flags
    archived: bool = sb.field(description="Archived")
    change_password_at_next_login: bool = sb.field(description="Change Password at Next Login")
    suspended: bool = sb.field(description="Suspended")

    # Read Only Attributes
    agreed_to_terms: bool = sb.field(description="Agreed to Google Terms of Service")
    is_enforced_in_2sv: sb.Private[bool] = sb.field(description="Is Enforced in 2SV")
    is_enrolled_in_2sv: sb.Private[bool] = sb.field(description="Is Enrolled in 2SV")
    org_unit_path: str = sb.field(description="Org Unit Path")

    # Security
    has_recovery_email: bool = sb.field(description="Has Recovery Email")
    has_recovery_phone: bool = sb.field(description="Has Recovery Phone")

    # Timestamps
    creation_time: datetime = sb.field(description="Creation Time")
    last_login_time: sb.Private[datetime] = sb.field(description="Last Login Time.")

    @sd.field(
        name="lastLoginTime",
        description="Last Login Time. Null if never logged in",
        only=["last_login_time"],
    )
    def nulled_creation_time(self) -> datetime | None:
        if self.last_login_time < datetime(1990, 1, 1, tzinfo=zoneinfo.ZoneInfo("UTC")):
            # If the last login time is before a certain date, we consider it as never logged in
            # If they somehow logged into Google in the 80s, then fair enough.
            return None
        return self.last_login_time

    @sd.field(
        description="Email Address Aliases",
        prefetch_related=["aliases"],
        extensions=[HasSourcePerm("workspace_account.view_pii", fail_silently=True)],
    )
    def aliases(self, info: sb.Info) -> list[str]:
        # note: this looks inefficient, but it is optimised by the above prefetch_related
        return [alias.address for alias in self.aliases.all()]

    @sd.field(
        description="Is 2SV correctly configured",
        only=["is_enforced_in_2sv", "is_enrolled_in_2sv"],
    )
    def is_2sv_configured(self) -> bool:
        return self.is_enforced_in_2sv and self.is_enrolled_in_2sv
