"""Person GraphQL filters (separate from ``graph_types`` to avoid import cycles with ``RoleFilter``)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import strawberry as sb
import strawberry_django as sd
from django.db.models import Exists, OuterRef, Q
from strawberry import UNSET
from strawberry.types.base import get_object_definition, has_object_definition
from strawberry_django import process_filters
from strawberry_django.utils.typing import has_django_definition

from salute.hierarchy.graphql.graph_filters import GroupFilter
from salute.people import models
from salute.roles.models import Role

if TYPE_CHECKING:
    from salute.roles.graphql.graph_filters import RoleFilter


def _filter_lookup_specified(lookup: Any) -> bool:
    """True if any *data* field on a strawberry-django filter lookup is set."""
    if lookup is UNSET or lookup is None:
        return False
    cls = type(lookup)
    definition = get_object_definition(cls, strict=False)
    if definition is None:
        return False
    for field in definition.fields:
        if field.base_resolver is not None:
            continue
        v = getattr(lookup, field.name, UNSET)
        if v is not UNSET and v is not None:
            return True
    return False


def group_filter_defines_criteria(value: GroupFilter) -> bool:
    if _filter_lookup_specified(getattr(value, "id", UNSET)):
        return True
    if _filter_lookup_specified(getattr(value, "local_unit_number", UNSET)):
        return True
    group_type = getattr(value, "group_type", UNSET)
    return group_type is not UNSET and group_type is not None


def _role_filter_defines_criteria(value: object) -> bool:
    """True if the role filter input constrains the role query at all."""
    if not has_django_definition(value):
        return False
    if _filter_lookup_specified(getattr(value, "id", UNSET)):
        return True
    inner = getattr(value, "group", UNSET)
    if inner is not UNSET and inner is not None and has_object_definition(inner):
        if group_filter_defines_criteria(inner):
            return True
    inner = getattr(value, "team", UNSET)
    if inner is not UNSET and inner is not None and has_object_definition(inner):
        return True
    inner = getattr(value, "person", UNSET)
    if inner is not UNSET and inner is not None and has_object_definition(inner):
        return True
    ia = getattr(value, "is_automatic", UNSET)
    if ia is not UNSET and ia is not None:
        return True
    return False


@sd.filter_type(models.Person, lookups=True)
class PersonFilter:
    id: sd.BaseFilterLookup[sb.relay.GlobalID] | None = sb.UNSET
    display_name: sb.auto = sb.UNSET

    @sd.filter_field(
        filter_none=True,
        description=(
            "Person has at least one role matching this filter. "
            "Use `group` on the nested role filter to match teams under those groups "
            "(group team, section team in the group, or sub-team of a group team)."
        ),
    )
    def has_role(self, value: RoleFilter | None, prefix: str) -> Q:
        if value is None or value is UNSET:
            return Q()
        if not _role_filter_defines_criteria(value):
            return Q(pk__in=[])
        _, inner_q = process_filters(value, Role.objects.all(), None)  # type: ignore
        if inner_q == Q():
            return Q(pk__in=[])
        return Q(Exists(Role.objects.filter(person_id=OuterRef(f"{prefix}pk")).filter(inner_q).only("id")))

    @sd.filter_field(description="Filter by search query")
    def search(self, value: str, prefix: str) -> Q:
        return Q(**{f"{prefix}display_name__icontains": value}) | Q(**{f"{prefix}membership_number__icontains": value})


# ``RoleFilter`` is assigned by ``salute.roles.graphql.graph_filters`` after that module loads
# (see module tail there); avoids a circular import if declared here.
