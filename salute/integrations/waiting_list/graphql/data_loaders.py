from __future__ import annotations

from collections import defaultdict
from uuid import UUID

from asgiref.sync import sync_to_async
from django.db import models
from django.db.models import Count
from strawberry.dataloader import DataLoader

from salute.hierarchy.models import Group, Section
from salute.integrations.waiting_list.models import WaitingListEntry


async def load_total_waiting_list_count_for_district(keys: list[UUID]) -> list[int]:
    """Get the total waiting list count for districts.

    Args:
        keys: List of district IDs.
    """

    def _get_district_counts(keys: list[UUID]) -> dict[UUID, int]:
        # Realistically, there is only one district, so the loop here exists
        # just to meet the dataloader interface pattern.
        results = {}

        # Process each unique district_id
        for district_id in set(keys):
            # Get the total waiting list count for the district
            # Note: Currently returns global count as there's typically only one district
            waiting_list_count = WaitingListEntry.objects.filter(successfully_transferred=False).count()

            results[district_id] = waiting_list_count

        return results

    # Get all counts in a single database query
    count_dict = await sync_to_async(lambda: _get_district_counts(keys))()

    # Return counts in the same order as the input keys
    return [count_dict[key] for key in keys]


async def load_total_waiting_list_count_for_groups(pks: list[UUID]) -> list[int | None]:
    """Load the total waiting list count for each group."""

    def _get_group_counts(pks: list[UUID]) -> dict[UUID, int]:
        # Query from Group side, using Count to aggregate waiting list entries
        # Relationship: Group -> WaitingListUnit (via group FK) -> WaitingListEntry (via M2M)
        # The filter parameter applies the condition at SQL level for efficiency
        # distinct=True ensures entries linked through multiple units are counted once per group
        group_counts = (
            Group.objects.filter(id__in=pks)
            .annotate(
                waiting_list_count=Count(
                    "waiting_list_units__waiting_list_entries",
                    filter=models.Q(waiting_list_units__waiting_list_entries__successfully_transferred=False),
                    distinct=True,
                )
            )
            .values_list("id", "waiting_list_count")
        )

        return dict(group_counts)

    count_dict = await sync_to_async(lambda: _get_group_counts(pks))()

    # Return counts in the same order as the input pks, with None for groups without records
    return [count_dict.get(pk) for pk in pks]


async def load_total_waiting_list_count_for_sections(pks: list[UUID]) -> list[int | None]:
    """Load the total waiting list count for each section."""

    def _get_section_counts(pks: list[UUID]) -> dict[UUID, int]:
        # Query from Section side, handling both Group and District sections
        # For Group sections: match entries where units__group matches section.group
        # For District sections: match entries where units__section matches section
        # Both also filter by target_section matching section.section_type.name
        # Optimized to avoid N+1 queries by doing bulk queries for each section type

        from django.utils import timezone

        sections = Section.objects.filter(id__in=pks).select_related("group")
        section_counts: dict[UUID, int] = {}

        # Split sections into group sections and district sections
        group_sections = [s for s in sections if s.group is not None]
        district_sections = [s for s in sections if s.group is None]

        # Base queryset with target_section annotation
        base_qs = WaitingListEntry.objects.with_target_section(timezone.now()).filter(successfully_transferred=False)

        # Process group sections in bulk
        if group_sections:
            # Group sections by section_type to minimize queries
            sections_by_type: dict[str, list[Section]] = defaultdict(list)
            for section in group_sections:
                sections_by_type[section.section_type.name].append(section)

            for section_type_name, type_sections in sections_by_type.items():
                # Get all group IDs for this section type
                group_ids = [s.group_id for s in type_sections if s.group_id]
                if not group_ids:
                    continue

                # Single query for all group sections of this type
                counts = (
                    base_qs.filter(
                        units__group_id__in=group_ids,
                        target_section=section_type_name,
                    )
                    .values("units__group_id")
                    .annotate(count=Count("id", distinct=True))
                    .values_list("units__group_id", "count")
                )

                # Map group_id back to section_id
                group_to_section = {s.group_id: s.id for s in type_sections if s.group_id}
                for group_id, count in counts:
                    if group_id in group_to_section:
                        section_counts[group_to_section[group_id]] = count

        # Process district sections in bulk
        if district_sections:
            # Group sections by section_type to minimize queries
            district_sections_by_type: dict[str, list[Section]] = defaultdict(list)
            for section in district_sections:
                district_sections_by_type[section.section_type.name].append(section)

            for section_type_name, type_sections in district_sections_by_type.items():
                # Get all section IDs for this section type
                section_ids = [s.id for s in type_sections]

                # Single query for all district sections of this type
                counts = (
                    base_qs.filter(
                        units__section_id__in=section_ids,
                        target_section=section_type_name,
                    )
                    .values("units__section_id")
                    .annotate(count=Count("id", distinct=True))
                    .values_list("units__section_id", "count")
                )

                # Map section_id to count
                for section_id, count in counts:
                    section_counts[section_id] = count

        return section_counts

    count_dict = await sync_to_async(lambda: _get_section_counts(pks))()

    # Return counts in the same order as the input pks, with None for sections without records
    return [count_dict.get(pk) for pk in pks]


def create_waiting_list_dataloaders() -> dict[str, DataLoader]:
    """Create a fresh set of data loaders for a new request context."""
    return {
        "total_waiting_list_count_for_districts": DataLoader(load_fn=load_total_waiting_list_count_for_district),
        "total_waiting_list_count_for_groups": DataLoader(load_fn=load_total_waiting_list_count_for_groups),
        "total_waiting_list_count_for_sections": DataLoader(load_fn=load_total_waiting_list_count_for_sections),
    }
