from __future__ import annotations

from datetime import date
from uuid import UUID

from asgiref.sync import sync_to_async
from django.db.models import F, Max, Q, Sum
from django.db.models.functions import TruncMonth, TruncWeek, TruncYear
from strawberry.dataloader import DataLoader

from salute.integrations.osm.graphql.graph_types import HeadcountAggregationPeriod
from salute.integrations.osm.models import OSMSectionHeadcountRecord


async def load_total_young_person_count_for_district(keys: list[tuple[UUID, bool]]) -> list[int]:
    """Get the total young person count for districts.

    Args:
        keys: List of tuples containing (district_id, direct_sections_only).
            If include_group_sections is True, also include sections from groups in the district.
            If False, only count sections that belong directly to the district.

    Returns:
        A list of total counts, one for each key in the input list.
    """

    def _get_district_counts(keys: list[tuple[UUID, bool]]) -> dict[tuple[UUID, bool], int]:
        # Realistically, there is only one district, so the loop here exists
        # just to meet the dataloader interface pattern.
        results = {}

        # Process each unique combination of district_id and include_group_sections
        for district_id, include_group_sections in set(keys):
            # Base query for sections in this district
            if include_group_sections:
                section_filter = Q(section__district_id=district_id) | Q(section__group__district_id=district_id)
            else:
                section_filter = Q(section__district_id=district_id, section__group__isnull=True)

            # Get the latest records for each section
            latest_dates = (
                OSMSectionHeadcountRecord.objects.filter(section_filter)
                .values("section_id")
                .annotate(latest_date=Max("date"))
            )

            # Get the total count using a join to the latest dates
            result = (
                OSMSectionHeadcountRecord.objects.filter(section_filter)
                .filter(
                    id__in=OSMSectionHeadcountRecord.objects.filter(
                        section_id__in=latest_dates.values("section_id")
                    ).filter(date__in=latest_dates.values("latest_date"))
                )
                .aggregate(total=Sum("young_person_count"))
            )

            results[(district_id, include_group_sections)] = result["total"] or 0

        return results

    # Get all counts in a single database query
    count_dict = await sync_to_async(lambda: _get_district_counts(keys))()

    # Return counts in the same order as the input keys
    return [count_dict[key] for key in keys]


async def load_latest_young_person_count_for_groups(pks: list[UUID]) -> list[int | None]:
    """Load the latest young person count for each group."""

    def _get_group_counts(pks: list[UUID]) -> dict[UUID, int]:
        # Get the latest records for each section
        latest_dates = (
            OSMSectionHeadcountRecord.objects.filter(section__group_id__in=pks)
            .values("section_id")
            .annotate(latest_date=Max("date"))
        )

        # Get the total count for each group using a join to the latest dates
        group_sums = (
            OSMSectionHeadcountRecord.objects.filter(section__group_id__in=pks)
            .filter(
                id__in=OSMSectionHeadcountRecord.objects.filter(
                    section_id__in=latest_dates.values("section_id")
                ).filter(date__in=latest_dates.values("latest_date"))
            )
            .values("section__group_id")
            .annotate(total_count=Sum("young_person_count"))
            .values_list("section__group_id", "total_count")
        )

        return dict(group_sums)

    count_dict = await sync_to_async(lambda: _get_group_counts(pks))()

    # Return counts in the same order as the input pks, with None for groups without records
    return [count_dict.get(pk) for pk in pks]


async def load_latest_young_person_count_for_sections(pks: list[UUID]) -> list[int | None]:
    """Load the latest young person count for each section."""

    # Get the latest records using sync_to_async since distinct() is sync-only
    def _get_section_counts(pks: list[UUID]) -> dict[UUID, int]:
        # Get the latest records for each section
        latest_dates = (
            OSMSectionHeadcountRecord.objects.filter(section_id__in=pks)
            .values("section_id")
            .annotate(latest_date=Max("date"))
        )

        # Get the latest count for each section
        section_counts = (
            OSMSectionHeadcountRecord.objects.filter(section_id__in=pks)
            .filter(
                id__in=OSMSectionHeadcountRecord.objects.filter(
                    section_id__in=latest_dates.values("section_id")
                ).filter(date__in=latest_dates.values("latest_date"))
            )
            .values_list("section_id", "young_person_count")
        )

        return dict(section_counts)

    count_dict = await sync_to_async(lambda: _get_section_counts(pks))()

    # Return counts in the same order as the input pks, with None for sections without records
    return [count_dict.get(pk) for pk in pks]


def headcount_for_sections(
    section_ids: list[UUID],
    start_date: date | None,
    end_date: date | None,
    period: HeadcountAggregationPeriod,
) -> dict[UUID, list[dict]]:
    """Load aggregated headcount data for multiple sections.

    This is the actual query function that fetches and aggregates data from the database.
    It's called by the DataLoader wrapper.

    Args:
        section_ids: List of section UUIDs to fetch data for
        start_date: Optional start date filter (inclusive)
        end_date: Optional end date filter (inclusive)
        period: Aggregation period (week, month, or year)

    Returns:
        Dictionary mapping section_id to list of data points
    """
    # Build query with date filters applied at the database level
    query = OSMSectionHeadcountRecord.objects.filter(section_id__in=section_ids)

    if start_date is not None:
        query = query.filter(date__gte=start_date)
    if end_date is not None:
        query = query.filter(date__lte=end_date)

    # Choose the appropriate truncation function based on period
    # For DAY, we don't need truncation - just use the date directly
    if period == HeadcountAggregationPeriod.DAY:
        aggregated_data = (
            query.annotate(period_start=F("date"))
            .values("section_id", "period_start")
            .annotate(
                young_person_count=Max("young_person_count"),
            )
            .order_by("section_id", "period_start")
        )
    else:
        trunc_functions = {
            HeadcountAggregationPeriod.WEEK: TruncWeek,
            HeadcountAggregationPeriod.MONTH: TruncMonth,
            HeadcountAggregationPeriod.YEAR: TruncYear,
        }
        trunc_func = trunc_functions[period]

        # Aggregate at the database level
        aggregated_data = (
            query.annotate(period_start=trunc_func("date"))
            .values("section_id", "period_start")
            .annotate(
                young_person_count=Max("young_person_count"),
            )
            .order_by("section_id", "period_start")
        )

    # Group results by section_id
    results: dict[UUID, list[dict]] = {sid: [] for sid in section_ids}
    for record in aggregated_data:
        section_id = record.pop("section_id")
        results[section_id].append(record)

    return results


async def load_headcount_for_sections(
    keys: list[tuple[UUID, date | None, date | None, HeadcountAggregationPeriod]],
) -> list[list[dict]]:
    """DataLoader wrapper for headcount data.

    Args:
        keys: List of tuples containing (section_id, start_date, end_date, period).
            All keys in a batch are expected to have the same start_date, end_date, and period.

    Returns:
        A list of lists, where each inner list contains dictionaries with
        period_start and young_person_count for that section.
    """
    # Extract section IDs and parameters (all keys have the same date range and period)
    section_ids = [key[0] for key in keys]
    start_date = keys[0][1] if keys else None
    end_date = keys[0][2] if keys else None
    period = keys[0][3] if keys else HeadcountAggregationPeriod.WEEK

    # Call the actual query function
    data_dict = await sync_to_async(lambda: headcount_for_sections(section_ids, start_date, end_date, period))()

    # Return results in the same order as input keys
    return [data_dict[key[0]] for key in keys]


def create_osm_dataloaders() -> dict[str, DataLoader]:
    """Create a fresh set of data loaders for a new request context."""
    return {
        "latest_young_person_count_for_sections": DataLoader(load_fn=load_latest_young_person_count_for_sections),
        "latest_young_person_count_for_groups": DataLoader(load_fn=load_latest_young_person_count_for_groups),
        "total_young_person_count_for_district": DataLoader(
            load_fn=load_total_young_person_count_for_district,
            cache_key_fn=lambda key: (key[0], key[1]),  # Use both district_id and include_group_sections as cache key
        ),
        "headcount_for_sections": DataLoader(
            load_fn=load_headcount_for_sections,
            cache_key_fn=lambda key: (key[0], key[1], key[2], key[3]),  # section_id, start_date, end_date, period
        ),
    }
