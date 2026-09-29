from uuid import UUID

from asgiref.sync import sync_to_async
from strawberry.dataloader import DataLoader

from salute.people.models import Person


async def load_latest_is_member_for_people(pks: list[UUID]) -> list[bool]:
    """Load the latest is_member status for each person."""

    def _get_member_status(pks: list[UUID]) -> dict[UUID, bool]:
        return dict(Person.objects.filter(id__in=pks).annotate_is_member().values_list("id", "is_member"))

    member_status_dict = await sync_to_async(lambda: _get_member_status(pks))()

    # Return member status in the same order as the input pks
    return [member_status_dict.get(pk, False) for pk in pks]


async def load_latest_is_included_in_census_for_people(pks: list[UUID]) -> list[bool]:
    """Load the latest is_included_in_census status for each person."""

    def _get_included_in_census_status(pks: list[UUID]) -> dict[UUID, bool]:
        return dict(
            Person.objects.filter(id__in=pks)
            .annotate_is_included_in_census()
            .values_list("id", "is_included_in_census")
        )

    included_in_census_status_dict = await sync_to_async(lambda: _get_included_in_census_status(pks))()

    # Return included in census status in the same order as the input pks
    return [included_in_census_status_dict.get(pk, False) for pk in pks]


async def load_days_of_service_for_people(pks: list[UUID]) -> list[int | None]:
    """Load the days of service for each person."""

    def _get_days_of_service(pks: list[UUID]) -> dict[UUID, int | None]:
        return dict(Person.objects.filter(id__in=pks).annotate_days_of_service().values_list("id", "days_of_service"))

    days_of_service_dict = await sync_to_async(lambda: _get_days_of_service(pks))()

    # Return days of service in the same order as the input pks
    return [days_of_service_dict.get(pk, None) for pk in pks]


def create_people_dataloaders() -> dict[str, DataLoader]:
    """Create a fresh set of data loaders for a new request context."""
    return {
        "latest_is_member_for_people": DataLoader(load_fn=load_latest_is_member_for_people),
        "latest_is_included_in_census_for_people": DataLoader(load_fn=load_latest_is_included_in_census_for_people),
        "days_of_service_for_people": DataLoader(load_fn=load_days_of_service_for_people),
    }
