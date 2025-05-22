import strawberry as sb
import strawberry_django as sd
from strawberry_django.permissions import HasPerm

from salute.locations import models as locations_models

from .graph_types import Site, SiteListConnection


@sb.type
class LocationsQuery:
    @sd.field(
        description="Get a site by ID",
        extensions=[HasPerm("site.view", message="You don't have permission to view that site.")],
    )
    def site(self, site_id: sb.relay.GlobalID, info: sb.Info) -> Site:
        return locations_models.Site.objects.filter(id=site_id.node_id)  # type: ignore[return-value]

    sites: SiteListConnection = sd.connection(
        description="List sites.",
        extensions=[HasPerm("site.list", message="You don't have permission to list sites.", fail_silently=False)],
    )
