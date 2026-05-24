from datetime import datetime
from typing import TYPE_CHECKING, Annotated

import strawberry as sb
import strawberry_django as sd

from salute.wifi import models

if TYPE_CHECKING:
    from salute.people.graphql.graph_types import Person


@sd.type(models.WifiAccountGroup)
class WifiAccountGroup(sb.relay.Node):
    name: sb.Private[str]
    slug: str
    description: str
    is_default: bool

    @sd.field(description="Formatted name for the WiFi account group", only="name")
    def display_name(self) -> str:
        return self.name


@sd.filter(models.WifiAccount)
class WifiAccountFilter:
    username: sd.StrFilterLookup | None = sb.UNSET
    is_active: sd.FilterLookup[bool] | None = sb.UNSET


@sd.type(models.WifiAccount, filters=WifiAccountFilter)
class WifiAccount(sb.relay.Node):
    person: Annotated["Person", sb.lazy("salute.people.graphql.graph_types")]
    group: WifiAccountGroup
    username: str
    password: str
    is_active: bool

    updated_at: datetime
