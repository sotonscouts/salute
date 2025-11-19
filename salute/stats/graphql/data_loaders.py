from __future__ import annotations

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


def create_stats_dataloaders() -> dict[str, DataLoader]:
    """Create a fresh set of data loaders for a new request context."""
    return {
        "latest_annual_subs_cost_for_sections": DataLoader(load_fn=load_latest_annual_subs_cost_for_sections),
    }
