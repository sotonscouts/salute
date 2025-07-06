from typing import Any

import strawberry as sb
import strawberry_django as sd
from django.conf import settings
from django.db.models import QuerySet

from salute.mailing_groups import models

from .graph_filters import SystemMailingGroupFilter


@sd.type(models.SystemMailingGroup, filters=SystemMailingGroupFilter)
class SystemMailingGroup(sb.relay.Node):
    name: sb.Private[str]
    display_name: str
    short_name: str = sd.field(
        description="The short name of the mailing group. Only use where context is clear.",
    )

    @sd.field(
        description="The address of the mailing group.",
        only=["name"],
    )
    def address(self) -> str:
        return f"{self.name}@{settings.GOOGLE_DOMAIN}"  # type: ignore[misc]

    @classmethod
    def get_queryset(cls, queryset: QuerySet, info: sb.Info, **kwargs: Any) -> QuerySet:
        return queryset.filter(workspace_group__isnull=False)
