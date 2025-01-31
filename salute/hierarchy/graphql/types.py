from __future__ import annotations

from uuid import UUID

import strawberry
import strawberry.extensions
import strawberry_django
from strawberry import auto, relay

from salute.hierarchy import models as hierarchy_models
from salute.people import models as people_models


@strawberry_django.type(hierarchy_models.District)
class District(relay.Node):
    id: relay.NodeID[UUID]
    unit_name: str = strawberry.field(description="Official Unit Name")
    display_name: str = strawberry_django.field(field_name="unit_name")
    shortcode: str = strawberry.field(description="")
    groups: strawberry_django.relay.ListConnectionWithTotalCount[Group] = strawberry_django.connection()
    sections: strawberry_django.relay.ListConnectionWithTotalCount[Section] = strawberry_django.connection()


@strawberry_django.type(hierarchy_models.Group)
class Group(relay.Node):
    id: relay.NodeID[UUID]
    unit_name: auto
    shortcode: auto
    district: District
    group_type: auto
    charity_number: auto
    local_unit_number: auto
    location_name: auto
    sections: strawberry_django.relay.ListConnectionWithTotalCount[Section] = strawberry_django.connection()


@strawberry_django.filter(hierarchy_models.Section, lookups=True)
class SectionFilter:
    unit_name: auto
    section_type: str | None = strawberry.UNSET


@strawberry_django.type(hierarchy_models.Section, filters=SectionFilter)
class Section(relay.Node):
    id: relay.NodeID[UUID]
    unit_name: auto
    shortcode: auto
    section_type: auto
    district: District | None
    group: Group | None


from strawberry.permission import BasePermission


class TestPermission(BasePermission):
    message = "User is not Dan"
    error_extensions = {"code": "NOT_DAN"}

    def has_permission(self, source, info, **kwargs):
        return source.display_name == "Dan Trickey"


@strawberry_django.filter(people_models.Person, lookups=True)
class PersonFilter:
    display_name: auto


@strawberry_django.type(people_models.Person, filters=PersonFilter)
class Person(relay.Node):
    id: relay.NodeID[UUID]
    first_name: str
    display_name: str
    formatted_membership_number: str = strawberry_django.field(only="membership_number")
    contact_email: str | None = strawberry_django.field(
        only="tsa_email",
        prefetch_related="workspace_account",
        extensions=[strawberry.permission.PermissionExtension([TestPermission()], fail_silently=True)],
    )
