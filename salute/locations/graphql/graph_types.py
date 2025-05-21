from __future__ import annotations

from typing import Any, cast

import strawberry as sb
import strawberry_django as sd
from django.db.models import QuerySet
from strawberry_django.auth.utils import get_current_user
from strawberry_django.permissions import HasPerm

from salute.accounts.models import User
from salute.hierarchy.graphql.graph_types import District, Group, Section
from salute.locations import models
from salute.locations.constants import TenureType


@sb.type(description="A geographic point.")
class Point:
    latitude: float
    longitude: float


@sd.type(models.SiteOperator)
class SiteOperator(sb.relay.Node):
    name: sb.Private[str]

    district: District | None
    group: Group | None

    sites: SiteListConnection = sd.connection(description="List operated sites.")

    @sd.field(only=["name"], select_related=["district", "group"])
    def display_name(self) -> str:
        return self.display_name  #

    @classmethod
    def get_queryset(
        cls, queryset: models.SiteOperatorQuerySet | QuerySet, info: sb.Info, **kwargs: Any
    ) -> models.SiteOperatorQuerySet | QuerySet:
        user = get_current_user(info)
        if not user.is_authenticated:
            return queryset.none()

        user = cast(User, user)
        # When the strawberry optimiser is determining the queryset relations, it will call this method.
        # In such calls, the queryset is not a SiteOperatorQuerySet, but a Django QuerySet.
        if hasattr(queryset, "for_user"):
            return queryset.for_user(user)
        return queryset


@sd.filter_type(models.Site, lookups=True)
class SiteFilter:
    id: sd.BaseFilterLookup[sb.relay.GlobalID] | None = sb.UNSET
    tenure_type: sb.auto = sb.UNSET


@sd.type(
    models.Site,
    filters=SiteFilter,
)
class Site(sb.relay.Node):
    name: sb.Private[str]

    operator: SiteOperator = sd.field(description="The operator of the site.")
    tenure_type: TenureType | None = sd.field(
        description="The tenure type of the site.",
        extensions=[
            HasPerm(
                "site.view_site_tenure_type",
                fail_silently=True,
                message="You don't have permission to view the tenure type of this site.",
            ),
        ],
    )

    uprn: str = sd.field(description="Unique Property Reference Number")
    building_name: str = sd.field(description="Building name")
    street_number: str = sd.field(description="Street number")
    street: str = sd.field(description="Street name")
    town: str = sd.field(description="Town")
    county: str = sd.field(description="County")
    postcode: str = sd.field(description="Postcode")

    latitude: sb.Private[float]
    longitude: sb.Private[float]

    groups: sd.relay.DjangoListConnection[Group] = sd.connection(
        description="List groups that use this site.",
        extensions=[sd.permissions.HasPerm("group.list", message="You don't have permission to list groups.")],
    )

    sections: sd.relay.DjangoListConnection[Section] = sd.connection(
        description="List sections that explicitly use this site.",
        extensions=[sd.permissions.HasPerm("section.list", message="You don't have permission to list groups.")],
    )

    @sd.field(only=["name"])
    def display_name(self) -> str:
        return self.name

    @sd.field(only=["latitude", "longitude"])
    def location(self) -> Point:
        return Point(latitude=self.latitude, longitude=self.longitude)

    @classmethod
    def get_queryset(
        cls, queryset: models.SiteQuerySet | QuerySet, info: sb.Info, **kwargs: Any
    ) -> models.SiteQuerySet | QuerySet:
        user = get_current_user(info)
        if not user.is_authenticated:
            return queryset.none()

        user = cast(User, user)
        # When the strawberry optimiser is determining the queryset relations, it will call this method.
        # In such calls, the queryset is not a SiteQuerySet, but a Django QuerySet.
        if hasattr(queryset, "for_user"):
            return queryset.for_user(user)
        return queryset


@sb.type(name="Connection", description="A connection to a list of items.")
class SiteListConnection(sd.relay.DjangoListConnection[Site]):
    @sd.field(description="The centroid of the sites. Some sites may be excluded from the calculation.")
    @sd.resolvers.django_resolver
    def centroid(self) -> Point | None:
        assert self.nodes is not None

        if isinstance(self.nodes, models.SiteQuerySet):
            centroid = self.nodes.filter(include_in_centroid_calculation=True).centroid()
            if centroid is None:
                return None
            return Point(latitude=centroid[0], longitude=centroid[1])

        return None
