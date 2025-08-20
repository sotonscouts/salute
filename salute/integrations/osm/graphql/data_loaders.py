from __future__ import annotations

from uuid import UUID

from asgiref.sync import sync_to_async
from django.db.models import Max, Q, Sum
from strawberry.dataloader import DataLoader

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


def create_osm_dataloaders() -> dict[str, DataLoader]:
    """Create a fresh set of data loaders for a new request context."""
    return {
        "latest_young_person_count_for_sections": DataLoader(load_fn=load_latest_young_person_count_for_sections),
        "latest_young_person_count_for_groups": DataLoader(load_fn=load_latest_young_person_count_for_groups),
        "total_young_person_count_for_district": DataLoader(
            load_fn=load_total_young_person_count_for_district,
            cache_key_fn=lambda key: (key[0], key[1]),  # Use both district_id and include_group_sections as cache key
        ),
    }
