from django.core.management.base import BaseCommand
from django.db.models import Count
from django.utils import timezone

from salute.roles.models import Team
from salute.stats.models import TeamSummaryRecord


class Command(BaseCommand):
    help = "Update team summary records"

    def handle(self, *args: tuple[str, ...], **options: dict[str, str]) -> None:
        teams = Team.objects.prefetch_related("roles", "accreditations").annotate(
            person_count=Count("roles__person", distinct=True),
        )
        now = timezone.now()
        today = now.date()

        for team in teams:
            summary_record, created = TeamSummaryRecord.objects.update_or_create(
                team=team,
                date=today,
                defaults={
                    "total_people": team.person_count,
                    "count_by_role_type": {
                        str(role_type["role_type"]): role_type["count"]
                        for role_type in team.roles.values("role_type").annotate(count=Count("id"))
                    },
                    "count_by_role_status": {
                        str(role_status["status"]): role_status["count"]
                        for role_status in team.roles.values("status").annotate(count=Count("id"))
                    },
                    "count_by_accreditation_type": {
                        str(accreditation_type["accreditation_type"]): accreditation_type["count"]
                        for accreditation_type in team.accreditations.values("accreditation_type").annotate(
                            count=Count("id")
                        )
                    },
                },
            )
