from typing import Any

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from salute.hierarchy.models import Section
from salute.integrations.waiting_list.client import AirTableClient
from salute.integrations.waiting_list.models import (
    WaitingListEntry,
    WaitingListSectionRecord,
    WaitingListSectionType,
    WaitingListSectionTypeRecord,
    WaitingListUnit,
)


class Command(BaseCommand):
    help = "Sync waiting list entries from Airtable into the database"

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Fetch data from Airtable but don't write to the database",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        api_key = settings.AIRTABLE_API_KEY  # type: ignore[misc]
        base_id = settings.AIRTABLE_BASE_ID  # type: ignore[misc]
        table_id = settings.AIRTABLE_TABLE_ID  # type: ignore[misc]

        client = AirTableClient(api_key=api_key, base_id=base_id, table_id=table_id)

        self.stdout.write("Fetching waiting list entries from Airtable...")
        entries = client.get_waiting_list()
        self.stdout.write(self.style.SUCCESS(f"Fetched {len(entries)} entries"))

        if options["dry_run"]:
            self.stdout.write(self.style.WARNING("Dry run mode - not writing to database"))
            for entry in entries:
                self.stdout.write(f"  - {entry.external_id}: {len(entry.groups_of_interest)} groups")
            return

        with transaction.atomic():
            synced_count = 0
            created_count = 0
            updated_count = 0

            for entry in entries:
                # Get or create WaitingListUnit objects for each group of interest
                units = []
                for group_name in entry.groups_of_interest:
                    unit, _created = WaitingListUnit.objects.get_or_create(name=group_name)
                    units.append(unit)

                joined_at = entry.joined_waiting_list_at
                if timezone.is_naive(joined_at):
                    joined_at = timezone.make_aware(joined_at)

                db_entry, created = WaitingListEntry.objects.update_or_create(
                    external_id=entry.external_id,
                    defaults={
                        "date_of_birth": entry.date_of_birth,
                        "postcode": entry.postcode or "",
                        "joined_waiting_list_at": joined_at,
                        "successfully_transferred": entry.successfully_transferred,
                    },
                )

                # Update the many-to-many relationship
                db_entry.units.set(units)

                synced_count += 1
                if created:
                    created_count += 1
                else:
                    updated_count += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f"Sync complete: {synced_count} entries synced ({created_count} created, {updated_count} updated)"
                )
            )

        for section in Section.objects.all():
            qs = WaitingListEntry.objects.with_target_section(timezone.now()).filter(successfully_transferred=False)
            if section.group is not None:
                qs = qs.filter(units__group=section.group, target_section=section.section_type.name)
            else:
                qs = qs.filter(units__section=section, target_section=section.section_type.name)
            WaitingListSectionRecord.objects.update_or_create(
                section=section,
                date=timezone.now().date(),
                defaults={"waiting_list_count": qs.count()},
            )

        for section_type in WaitingListSectionType:
            qs = WaitingListEntry.objects.with_target_section(timezone.now()).filter(
                successfully_transferred=False, target_section=section_type.value
            )
            WaitingListSectionTypeRecord.objects.update_or_create(
                section_type=section_type.value,
                date=timezone.now().date(),
                defaults={"waiting_list_count": qs.count()},
            )

        self.stdout.write(self.style.SUCCESS("Waiting list section records updated"))
