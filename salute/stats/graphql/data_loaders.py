from __future__ import annotations

from collections import defaultdict
from uuid import UUID

from asgiref.sync import sync_to_async
from django.db.models import Max
from strawberry.dataloader import DataLoader

from salute.stats.models import SectionCensusReturn


async def load_latest_annual_subs_cost_for_sections(pks: list[UUID]) -> list[int | None]:
    """Load the latest annual subscription cost for each section."""

    # Get the latest records using sync_to_async since distinct() is sync-only
    def _get_section_costs(pks: list[UUID]) -> dict[UUID, int]:
        # Get the latest records for each section
        latest_dates = (
            SectionCensusReturn.objects.filter(section_id__in=pks)
            .values("section_id")
            .annotate(latest_date=Max("year"))
        )

        # Get the latest count for each section
        section_counts = (
            SectionCensusReturn.objects.filter(section_id__in=pks)
            .filter(
                id__in=SectionCensusReturn.objects.filter(section_id__in=latest_dates.values("section_id")).filter(
                    year__in=latest_dates.values("latest_date")
                )
            )
            .values_list("section_id", "annual_subs_cost")
        )

        return dict(section_counts)

    count_dict = await sync_to_async(lambda: _get_section_costs(pks))()

    # Return costs in the same order as the input pks, with None for sections without records
    return [count_dict.get(pk) for pk in pks]


async def load_census_returns_for_sections(
    keys: list[tuple[UUID, int | None, int | None]],
) -> list[list[SectionCensusReturn]]:
    """Load census returns for each section, ordered by year ascending.

    Args:
        keys: List of tuples containing (section_id, start_year, end_year).
            All keys in a batch are expected to have the same start_year and end_year.
            start_year and end_year can be None.

    Returns:
        A list of lists, where each inner list contains SectionCensusReturn objects
        for that section, ordered by year ascending.
    """
    # Extract section IDs and parameters (all keys have the same year range)
    if not keys:
        return []
    section_ids = [section_id for section_id, _, _ in keys]
    _, start_year, end_year = keys[0]

    def _get_census_returns(
        pks: list[UUID], start_year: int | None, end_year: int | None
    ) -> dict[UUID, list[SectionCensusReturn]]:
        query = SectionCensusReturn.objects.filter(section_id__in=pks)
        if start_year is not None:
            query = query.filter(year__gte=start_year)
        if end_year is not None:
            query = query.filter(year__lte=end_year)

        # Order by year ascending
        census_returns = query.order_by("year")

        # Group by section_id
        result: defaultdict[UUID, list[SectionCensusReturn]] = defaultdict(list)
        for census_return in census_returns:
            result[census_return.section_id].append(census_return)
        return dict(result)

    census_returns_dict = await sync_to_async(lambda: _get_census_returns(section_ids, start_year, end_year))()

    # Return results in the same order as input keys
    return [census_returns_dict.get(section_id, []) for section_id, _, _ in keys]


def create_stats_dataloaders() -> dict[str, DataLoader]:
    """Create a fresh set of data loaders for a new request context."""
    return {
        "latest_annual_subs_cost_for_sections": DataLoader(load_fn=load_latest_annual_subs_cost_for_sections),
        "census_returns_for_sections": DataLoader(
            load_fn=load_census_returns_for_sections,
            cache_key_fn=lambda key: key,  # (section_id, start_year, end_year)
        ),
    }
