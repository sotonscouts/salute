import strawberry as sb
import strawberry_django as sd
from django.conf import settings

from salute.mailing_groups import models


@sd.type(models.SystemMailingGroup)
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
