from __future__ import annotations

from typing import Any

from django.http import HttpRequest
from strawberry.django.context import StrawberryDjangoContext

from salute.integrations.osm.graphql.data_loaders import create_osm_dataloaders
from salute.people.graphql.data_loaders import create_people_dataloaders
from salute.roles.graphql.data_loaders import create_roles_dataloaders
from salute.stats.graphql.data_loaders import create_stats_dataloaders


class SaluteContext(StrawberryDjangoContext):
    def __init__(self, request: HttpRequest, response: Any = None, **kwargs: Any) -> None:
        super().__init__(request=request, response=response, **kwargs)
        self.roles = create_roles_dataloaders()
        self.osm_dataloaders = create_osm_dataloaders()
        self.stats_dataloaders = create_stats_dataloaders()
        self.people_dataloaders = create_people_dataloaders()
