# mypy: disable-error-code="misc"
from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

import strawberry as sb
import strawberry_django as sd
from django.db.models import Case, OrderBy, QuerySet, Value, When
from strawberry import auto
from strawberry_django.permissions import HasPerm

from salute.hierarchy import models
from salute.hierarchy.constants import SECTION_TYPE_INFO, SectionOperatingCategory, SectionType, Weekday

if TYPE_CHECKING:
    from salute.roles.graphql.graph_types import DistrictTeam, GroupTeam, SectionTeam


@sb.interface
class Unit:
    unit_name: str = sd.field(description="Official name of the unit")
    shortcode: str = sd.field(description="Shortcode reference for the unit")
    display_name: str


@sd.type(models.District)
class District(Unit, sb.relay.Node):
    display_name: str = sd.field(description="Formatted name for the unit", only="unit_name")
    groups: sd.relay.ListConnectionWithTotalCount[Group] = sd.connection()
    sections: sd.relay.ListConnectionWithTotalCount[DistrictSection] = sd.connection()
    teams: list[Annotated[DistrictTeam, sb.lazy("salute.roles.graphql.graph_types")]] = sd.field(
        extensions=[HasPerm("team.list", message="You don't have permission to list teams.")]
    )


@sd.order(models.Group)
class GroupOrder:
    local_unit_number: auto


@sd.filter(models.Group)
class GroupFilter:
    group_type: models.GroupType


@sd.type(
    models.Group,
    order=GroupOrder,  # type: ignore[literal-required]
    filters=GroupFilter,
)
class Group(Unit, sb.relay.Node):
    display_name: str = sd.field(description="Formatted name for the unit", only=["local_unit_number", "location_name"])

    district: District
    group_type: models.GroupType
    charity_number: int | None

    ordinal: str = sd.field(description="Ordinal for the group", only=["local_unit_number"])
    # location_name intentionally excluded whilst we work out data modelling for it
    # local_unit_number intentionally excluded in favour of ordinal

    sections: sd.relay.ListConnectionWithTotalCount[GroupSection] = sd.connection()
    teams: list[Annotated[GroupTeam, sb.lazy("salute.roles.graphql.graph_types")]] = sd.field(
        extensions=[HasPerm("team.list", message="You don't have permission to list teams.")]
    )


@sd.order(models.Section)
class SectionOrder:
    group: GroupOrder

    @sd.order_field(description="Order in ascending age of section type")
    def section_type(
        self,
        info: sb.Info,
        queryset: QuerySet[models.Section],
        value: sd.Ordering,
        prefix: str,
        sequence: dict[str, sd.Ordering] | None,
    ) -> tuple[QuerySet[models.Section], list[OrderBy]]:
        queryset = queryset.alias(
            _ordered__section_num=Case(
                *[When(section_type=val, then=Value(idx)) for idx, val in enumerate(SectionType)]
            )
        )
        ordering = value.resolve(f"{prefix}_ordered__section_num")
        return queryset, [ordering]

    @sd.order_field(description="Order by usual weekday")
    def usual_weekday(
        self,
        info: sb.Info,
        queryset: QuerySet[models.Section],
        value: sd.Ordering,
        prefix: str,
        sequence: dict[str, sd.Ordering] | None,
    ) -> tuple[QuerySet[models.Section], list[OrderBy]]:
        queryset = queryset.alias(
            _ordered__weekday_num=Case(*[When(usual_weekday=val, then=Value(idx)) for idx, val in enumerate(Weekday)])
        )
        ordering = value.resolve(f"{prefix}_ordered__weekday_num")
        return queryset, [ordering]


@sd.filter(models.Section, lookups=True)
class SectionFilter:
    section_type: sb.auto
    usual_weekday: sb.auto
    group: GroupFilter | None = sd.filter_field(
        filter_none=True, description="Filter by group. Set to null for district sections"
    )


@sd.interface(models.Section)
class Section(Unit, sb.relay.Node):
    display_name: str = sd.field(
        description="Formatted name for the unit",
        only=["usual_weekday", "section_type", "nickname"],
        select_related=["group", "district"],
    )
    section_type: sb.Private[models.SectionType]
    usual_weekday: models.Weekday | None

    @sd.field(
        description="Get the team for the section",
        prefetch_related=["teams"],
        extensions=[HasPerm("team.list", message="You don't have permission to view teams.")],
    )
    def team(self, info: sb.Info) -> Annotated[SectionTeam, sb.lazy("salute.roles.graphql.graph_types")]:
        # A section should only have one team.
        return self.teams.first()  # type: ignore[attr-defined]

    @sd.field
    def section_type_info(self) -> SectionTypeInfo:
        sti = SECTION_TYPE_INFO[self.section_type]
        return SectionTypeInfo(
            value=self.section_type,
            **sti,
        )


@sd.type(
    models.Section,
    order=SectionOrder,  # type: ignore[literal-required]
    filters=SectionFilter,
)
class DistrictSection(Section):
    district: District


@sd.type(
    models.Section,
    order=SectionOrder,  # type: ignore[literal-required]
    filters=SectionFilter,
)
class GroupSection(Section):
    group: Group


@sd.type(
    models.Section,
    order=SectionOrder,  # type: ignore[literal-required]
    filters=SectionFilter,
)
class DistrictOrGroupSection(Section):
    """
    It's not possible to persuade Strawberry to let us return a union type on a sb.relay connection currently.

    So, when listing all sections, we just provide both values.
    """

    district: District | None
    group: Group | None


@sb.type
class SectionTypeInfo:
    value: SectionType = sb.field()
    display_name: str
    operating_category: SectionOperatingCategory

    # Hide the min and max age from the API for now
    min_age: sb.Private[str]
    max_age: sb.Private[str]

    @sb.field
    def formatted_age_range(self) -> str:
        return f"{self.min_age} - {self.max_age} years"
