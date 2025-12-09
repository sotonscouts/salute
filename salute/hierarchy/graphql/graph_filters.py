# mypy: disable-error-code="misc"
from __future__ import annotations

import strawberry as sb
import strawberry_django as sd

from salute.hierarchy import models
from salute.hierarchy.constants import SectionType


@sd.filter_type(models.Group)
class GroupFilter:
    id: sd.BaseFilterLookup[sb.relay.GlobalID] | None = sb.UNSET
    local_unit_number: sd.ComparisonFilterLookup[int] | None = sb.UNSET
    group_type: models.GroupType | None = sb.UNSET


@sd.filter_type(models.Section)
class SectionFilter:
    id: sd.BaseFilterLookup[sb.relay.GlobalID] | None = sb.UNSET
    section_type: sd.BaseFilterLookup[SectionType] | None = sb.UNSET
    usual_weekday: sd.BaseFilterLookup[models.Weekday] | None = sb.UNSET
    group: GroupFilter | None = sd.filter_field(
        filter_none=True, description="Filter by group. Set to null for district sections"
    )
