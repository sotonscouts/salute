import strawberry as sb
import strawberry_django as sd
from strawberry_django.permissions import HasPerm

from salute.mailing_groups import models as mailing_groups_models

from .graph_types import SystemMailingGroup


@sb.type
class MailingGroupsQuery:
    @sd.field(
        description="Get a system mailing group by ID",
        extensions=[
            HasPerm("system_mailing_group.view", message="You don't have permission to view that mailing group.")
        ],
        deprecation_reason="Use the `system_mailing_groups` field instead.",
    )
    def system_mailing_group(self, system_mailing_group_id: sb.relay.GlobalID, info: sb.Info) -> SystemMailingGroup:
        return mailing_groups_models.SystemMailingGroup.objects.filter(id=system_mailing_group_id.node_id)  # type: ignore[return-value]

    system_mailing_groups: sd.relay.DjangoListConnection[SystemMailingGroup] = sd.connection(
        description="List system mailing groups.",
        extensions=[
            HasPerm(
                "system_mailing_group.list",
                message="You don't have permission to list system mailing groups.",
                fail_silently=False,
            )
        ],
    )
