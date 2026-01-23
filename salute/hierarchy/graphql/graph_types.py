# mypy: disable-error-code="misc"
from __future__ import annotations

import datetime
from datetime import time
from decimal import Decimal
from string import Template
from typing import TYPE_CHECKING, Annotated

import strawberry as sb
import strawberry_django as sd
from django.conf import settings
from django.db.models import Case, Count, OrderBy, QuerySet, Value, When
from strawberry import auto
from strawberry_django.permissions import HasPerm

from salute.hierarchy import models
from salute.hierarchy.constants import SECTION_TYPE_INFO, SectionOperatingCategory, SectionType, Weekday
from salute.integrations.osm.graphql.graph_types import HeadcountAggregationPeriod, HeadcountDataPoint
from salute.mailing_groups import models as mailing_groups_models
from salute.people.models import Person
from salute.roles.models import Role
from salute.stats.graphql.graphql_types import SectionCensusReturn as SectionCensusReturnType

from .graph_filters import GroupFilter, SectionFilter

if TYPE_CHECKING:
    from salute.locations.graphql.graph_types import Site
    from salute.mailing_groups.graphql.graph_types import SystemMailingGroup
    from salute.roles.graphql.graph_types import DistrictTeam, GroupTeam, SectionTeam


@sb.interface
class Unit:
    unit_name: str = sd.field(description="Official name of the unit")
    shortcode: str = sd.field(description="Shortcode reference for the unit")
    display_name: str

    @sd.field(
        description="Link to the TSA unit details.",
        only="tsa_id",
    )
    def tsa_details_link(self) -> str:
        template = Template(settings.TSA_UNIT_LINK_TEMPLATE)
        return template.safe_substitute(tsaid=self.tsa_id)  # type: ignore[attr-defined]


@sd.type(models.District)
class District(Unit, sb.relay.Node):
    display_name: str = sd.field(description="Formatted name for the unit", only="unit_name")
    groups: sd.relay.DjangoListConnection[Group] = sd.connection()
    sections: sd.relay.DjangoListConnection[DistrictSection] = sd.connection()
    teams: list[Annotated[DistrictTeam, sb.lazy("salute.roles.graphql.graph_types")]] = sd.field(
        extensions=[HasPerm("team.list", message="You don't have permission to list teams.")]
    )

    @sd.field(description="Count of groups in this district.", annotate={"group_count": Count("groups", distinct=True)})
    def total_groups_count(self) -> int:
        return self.group_count  # type: ignore[attr-defined]

    @sd.field(
        description="Count of all people in this district, including in groups",
    )
    def total_people_count(
        self,
        *,
        is_member: bool | None = sb.UNSET,
        is_included_in_census: bool | None = sb.UNSET,
    ) -> int:
        """
        Count of all people in this district, including in groups.

        Assumes only one district in the database.
        """
        qs = Person.objects.all()

        if is_member is not sb.UNSET:
            qs = qs.annotate_is_member().filter(is_member=is_member)

        if is_included_in_census is not sb.UNSET:
            qs = qs.annotate_is_included_in_census().filter(is_included_in_census=is_included_in_census)

        return qs.count()

    @sd.field(
        description="Count of all people in this district, including in groups",
    )
    def total_roles_count(self) -> int:
        """
        Count of all roles in this district, including in groups.

        Assumes only one district in the database.
        """
        return Role.objects.count()

    @sd.field(
        description="Count of all sections in this district, including both direct district sections and sections in groups within the district",  # noqa: E501
        annotate={
            "direct_section_count": Count("sections", distinct=True),
            "group_section_count": Count("groups__sections", distinct=True),
        },
    )
    def total_sections_count(self) -> int:
        return self.direct_section_count + self.group_section_count  # type: ignore[attr-defined]

    @sd.field(
        description=("The young person count for the district. Data sourced from OSM."),
        only=["pk"],
        extensions=[
            HasPerm(
                "district.view_young_person_count",
                message="You don't have permission to view the young person count for this district.",
                fail_silently=True,
            )
        ],
    )
    async def young_person_count(
        self,
        info: sb.Info,
        *,
        include_group_sections: bool = True,
    ) -> int | None:
        """Get the young person count for the district.

        Args:
            include_group_sections: If True (default), includes sections in groups.
                If False, only counts sections directly in the district.
        """
        return await info.context.osm_dataloaders["total_young_person_count_for_district"].load(
            (self.pk, include_group_sections)  # type: ignore[attr-defined]
        )

    @sd.field(
        description=(
            "Total member count for the district. "
            "Includes adult members (people with member roles), young people (from OSM), "
            "and unique people with network member roles (is_youth_member=True). "
            "Note: This may double count individuals who are both adult members and have a network member role."
        ),
        only=["pk"],
        extensions=[
            HasPerm(
                "district.view_young_person_count",
                message="You don't have permission to view the member count for this district.",
                fail_silently=True,
            )
        ],
    )
    async def total_member_count(
        self,
        info: sb.Info,
    ) -> int | None:
        """Get the total member count for the district.

        This is a number that Hants County uses to report.

        This includes:
        - Adult (Censused) members (people with is_included_in_census=True roles)
        - Young people (from OSM data)
        - Unique people with youth member roles (is_youth_member=True roles)
        """
        from asgiref.sync import sync_to_async

        # Count adult members (distinct people with is_member_role=True roles)
        def _count_adult_members() -> int:
            return Person.objects.annotate_is_included_in_census().filter(is_included_in_census=True).count()

        # Count unique people with youth member roles (is_youth_member=True)
        def _count_youth_members() -> int:
            return Person.objects.annotate_is_youth_member().filter(is_youth_member=True).count()

        adult_member_count = await sync_to_async(_count_adult_members)()
        youth_member_count = await sync_to_async(_count_youth_members)()
        young_person_count_result = await info.context.osm_dataloaders["total_young_person_count_for_district"].load(
            (self.pk, True)  # type: ignore[attr-defined]
        )

        if young_person_count_result is None:
            return None

        return adult_member_count + young_person_count_result + youth_member_count


@sd.order_type(models.Group)
class GroupOrder:
    local_unit_number: auto


@sd.type(
    models.Group,
    ordering=GroupOrder,
    filters=GroupFilter,
)
class Group(Unit, sb.relay.Node):
    display_name: str = sd.field(description="Formatted name for the unit", only=["local_unit_number", "location_name"])
    public_name: str = sd.field(
        description="Public name for the unit", only=["local_unit_number", "location_name"], select_related=["locality"]
    )

    district: District
    group_type: models.GroupType
    charity_number: int | None

    ordinal: str = sd.field(description="Ordinal for the group", only=["local_unit_number"])
    primary_site: Annotated[Site, sb.lazy("salute.locations.graphql.graph_types")]
    # local_unit_number intentionally excluded in favour of ordinal

    sections: sd.relay.DjangoListConnection[GroupSection] = sd.connection()
    teams: list[Annotated[GroupTeam, sb.lazy("salute.roles.graphql.graph_types")]] = sd.field(
        extensions=[HasPerm("team.list", message="You don't have permission to list teams.")]
    )

    @sd.field(
        description="The latest young person count for the group. Data sourced from OSM.",
        only=["pk"],
        extensions=[
            HasPerm(
                "group.view_young_person_count",
                message="You don't have permission to view the young person count for this group.",
                fail_silently=True,
            )
        ],
    )
    async def young_person_count(self, info: sb.Info) -> int | None:
        return await info.context.osm_dataloaders["latest_young_person_count_for_groups"].load(self.pk)  # type: ignore[attr-defined]

    @sd.field(
        description="The system mailing groups that are important for this group. Only returns fully configured mailing groups.",  # noqa: E501
        deprecation_reason="Use system_mailing_groups with a filter instead.",
    )
    def system_mailing_groups(
        self,
    ) -> list[Annotated[SystemMailingGroup, sb.lazy("salute.mailing_groups.graphql.graph_types")]]:
        leadership_team = self.teams.filter(team_type__tsa_id="c30f4d78-a1f8-ed11-8f6d-6045bdd0ed08").first()  # type: ignore[attr-defined]
        if leadership_team is None:
            return []

        return mailing_groups_models.SystemMailingGroup.objects.filter(
            teams=leadership_team, workspace_group__isnull=False
        ).order_by("name")  # type: ignore[return-value]


@sb.type
class TimeRange:
    start: time
    end: time


@sd.order_type(models.Section)
class SectionOrder:
    group: GroupOrder

    @sd.order_field(description="Order in ascending age of section type")
    def section_type(
        self,
        info: sb.Info,
        queryset: QuerySet[models.Section],
        value: sd.Ordering,
        prefix: str,
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
    ) -> tuple[QuerySet[models.Section], list[OrderBy]]:
        queryset = queryset.alias(
            _ordered__weekday_num=Case(*[When(usual_weekday=val, then=Value(idx)) for idx, val in enumerate(Weekday)])
        )
        ordering = value.resolve(f"{prefix}_ordered__weekday_num")
        return queryset, [ordering]


@sd.type(models.Section, filters=SectionFilter)
class Section(Unit, sb.relay.Node):
    display_name: str = sd.field(
        description="Formatted name for the unit",
        only=["usual_weekday", "section_type", "nickname"],
        select_related=["group", "district"],
    )
    section_type: sb.Private[models.SectionType]
    usual_weekday: models.Weekday | None

    @sd.field(description="The usual meeting slot for the section", only=["usual_meeting_slot"])
    def usual_meeting_slot(self) -> TimeRange | None:
        if self.usual_meeting_slot is not None:
            return TimeRange(
                start=self.usual_meeting_slot.lower,
                end=self.usual_meeting_slot.upper,
            )
        return None

    @sd.field(
        description="Get the site for the section",
        select_related=["site"],
    )
    def site(self, info: sb.Info) -> Annotated[Site, sb.lazy("salute.locations.graphql.graph_types")] | None:
        if self.site is not None:
            return self.site

        # TODO: Optimise this query
        if self.group is not None:  # type: ignore[attr-defined]
            return self.group.primary_site  # type: ignore[attr-defined]

        # Network sections don't have a site
        return None

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
            display_name=sti["display_name"],
            operating_category=sti["operating_category"],
            min_age=sti["min_age"],
            max_age=sti["max_age"],
        )

    @sd.field(
        description="The latest young person count for the section. Data sourced from OSM.",
        only=["pk"],
        extensions=[
            HasPerm(
                "section.view_young_person_count",
                message="You don't have permission to view the young person count for this section.",
                fail_silently=True,
            )
        ],
    )
    async def young_person_count(self, info: sb.Info) -> int | None:
        return await info.context.osm_dataloaders["latest_young_person_count_for_sections"].load(self.pk)  # type: ignore[attr-defined]

    @sd.field(
        description="The annual subscription cost for the section from the latest census return.",
        only=["pk"],
    )
    async def annual_subs_cost(self, info: sb.Info) -> Decimal | None:
        return await info.context.stats_dataloaders["latest_annual_subs_cost_for_sections"].load(self.pk)  # type: ignore[attr-defined]

    @sd.field(
        description=(
            "Headcount data for the section, aggregated by the specified period with maximum counts. "
            "Data sourced from OSM."
        ),
        only=["pk"],
        extensions=[
            HasPerm(
                "section.view_young_person_count",
                message="You don't have permission to view the headcount data for this section.",
                fail_silently=True,
            )
        ],
    )
    async def headcount_history(
        self,
        info: sb.Info,
        *,
        period: HeadcountAggregationPeriod = HeadcountAggregationPeriod.WEEK,
        start_date: datetime.date | None = sb.UNSET,
        end_date: datetime.date | None = sb.UNSET,
    ) -> list[HeadcountDataPoint]:
        """Get headcount history for the section, aggregated by the specified period.

        Args:
            period: Aggregation period (week, month, or year). Defaults to week.
            start_date: Optional start date to filter results (inclusive).
            end_date: Optional end date to filter results (inclusive).
        """
        # Convert UNSET to None for the dataloader
        start = None if start_date is sb.UNSET else start_date
        end = None if end_date is sb.UNSET else end_date

        data = await info.context.osm_dataloaders["headcount_for_sections"].load(
            (self.pk, start, end, period)  # type: ignore[attr-defined]
        )
        return [
            HeadcountDataPoint(
                period_start=item["period_start"],
                young_person_count=item["young_person_count"],
            )
            for item in data
        ]

    @sd.field(
        description="Census returns for the section, ordered by year ascending.",
        only=["pk"],
        extensions=[
            HasPerm(
                "section.view_census_returns",
                message="You don't have permission to view the census returns for this section.",
                fail_silently=True,
            )
        ],
    )
    async def census_returns(
        self, info: sb.Info, *, start_year: int | None = sb.UNSET, end_year: int | None = sb.UNSET
    ) -> list[SectionCensusReturnType]:
        start = None if start_year is sb.UNSET else start_year
        end = None if end_year is sb.UNSET else end_year

        census_returns = await info.context.stats_dataloaders["census_returns_for_sections"].load(
            (self.pk, start, end)  # type: ignore[attr-defined]
        )
        return [
            SectionCensusReturnType(
                year=census_return.year,
                annual_subs_cost=census_return.annual_subs_cost,
                total_volunteers=census_return.total_volunteers,
                total_young_people=census_return.total_young_people,
                ratio_young_people_to_volunteers=census_return.ratio_young_people_to_volunteers,
            )
            for census_return in census_returns
        ]


@sd.type(
    models.Section,
    ordering=SectionOrder,
    filters=SectionFilter,
)
class DistrictSection(Section):
    district: District


@sd.type(
    models.Section,
    ordering=SectionOrder,
    filters=SectionFilter,
)
class GroupSection(Section):
    group: Group


@sd.type(
    models.Section,
    ordering=SectionOrder,
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
