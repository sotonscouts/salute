from __future__ import annotations

from django.db.models import Count
from strawberry.dataloader import DataLoader

from salute.roles.models import Team


async def load_person_count(pks: list[int]) -> list[int]:
    count_dict = {}

    async for team in (
        Team.objects.filter(
            pk__in=pks,
        )
        .only(
            "pk",
        )
        .annotate(
            person_count=Count("roles__person", distinct=True),
        )
    ):
        count_dict[team.pk] = team.person_count

    return [count_dict.get(pk, 0) for pk in pks]


def create_roles_dataloaders() -> dict[str, DataLoader]:
    """Create a fresh set of data loaders for a new request context."""
    return {
        "person_count": DataLoader(load_fn=load_person_count),
    }
