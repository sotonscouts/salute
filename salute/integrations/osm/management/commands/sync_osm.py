from typing import Any

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand
from django.utils import timezone

from salute.hierarchy.models import Section
from salute.integrations.osm.client import OSMClient, get_access_token
from salute.integrations.osm.models import OSMSectionHeadcountRecord, OSMSyncLog


class Command(BaseCommand):
    help = "Sync OSM data"

    def handle(self, *args: Any, **options: Any) -> None:
        client_id = settings.OSM_CLIENT_ID  # type: ignore[misc]
        client_secret = settings.OSM_CLIENT_SECRET  # type: ignore[misc]
        access_token = get_access_token(client_id, client_secret)
        client = OSMClient(access_token)

        # Get section data from OSM
        response = client.get_counts(section_id=settings.OSM_DISTRICT_SECTION_ID)  # type: ignore[misc]

        # Create sync log
        today = timezone.now().date()
        log, _created = OSMSyncLog.objects.update_or_create(
            date=today,
            defaults={"success": False, "data": response.model_dump()},
        )

        # Update section headcount records
        for osm_section in response.iter_sections():
            try:
                section = Section.objects.get(osm_id=osm_section.section_id)
            except ObjectDoesNotExist:
                self.stderr.write(
                    self.style.ERROR(f'Section "{osm_section.name}" with OSM ID {osm_section.section_id} not found')
                )
                continue

            OSMSectionHeadcountRecord.objects.update_or_create(
                section_id=section.id,
                date=today,
                defaults={
                    "young_person_count": osm_section.young_person_count,
                    "adult_count": osm_section.adult_count or 0,
                    "sync_log": log,
                },
            )

        log.success = True
        log.save()
