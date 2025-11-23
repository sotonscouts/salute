from typing import Any

from django.core.management.base import BaseCommand
from django.db import models
from django.db.models import Count, QuerySet
from django.utils import timezone

from salute.hierarchy.models import District, Group, Section
from salute.people.models import Person
from salute.roles.models import Accreditation, Role, Team
from salute.stats.models import DistrictSummaryRecord, GroupSummaryRecord, SectionSummaryRecord, TeamSummaryRecord


class Command(BaseCommand):
    help = "Update team summary records"

    def handle(self, *args: tuple[str, ...], **options: dict[str, str]) -> None:
        now = timezone.now()
        today = now.date()

        district = District.objects.get()
        DistrictSummaryRecord.objects.update_or_create(
            district=district,
            date=today,
            defaults={
                **self.get_summary_data_for_queryset(Team.objects.filter(district=district)),
                **self.get_summary_data_for_queryset(Team.objects.all(), key_suffix="_with_sub_units"),
            },
        )

        for group in Group.objects.all():
            group_teams = Team.objects.filter(models.Q(group=group) | models.Q(parent_team__group=group))
            group_teams_with_sub_units = Team.objects.filter(
                models.Q(group=group) | models.Q(section__group=group) | models.Q(parent_team__group=group)
            )
            GroupSummaryRecord.objects.update_or_create(
                group=group,
                date=today,
                defaults={
                    **self.get_summary_data_for_queryset(group_teams),
                    **self.get_summary_data_for_queryset(group_teams_with_sub_units, key_suffix="_with_sub_units"),
                },
            )

        for section in Section.objects.all():
            SectionSummaryRecord.objects.update_or_create(
                section=section,
                date=today,
                defaults={
                    **self.get_summary_data_for_queryset(Team.objects.filter(section=section)),
                    **self.get_summary_data_for_queryset(Team.objects.none(), key_suffix="_with_sub_units"),
                },
            )

        for team in Team.objects.all():
            TeamSummaryRecord.objects.update_or_create(
                team=team,
                date=today,
                defaults=self.get_summary_data_for_queryset(Team.objects.filter(id=team.id)),
            )

    def get_summary_data_for_queryset(self, team_qs: QuerySet[Team], *, key_suffix: str = "") -> dict[str, Any]:
        roles = Role.objects.filter(team__in=team_qs)
        accreditations = Accreditation.objects.filter(team__in=team_qs)
        people = Person.objects.filter(id__in=roles.values("person"))

        return {
            f"total_people{key_suffix}": people.count(),
            f"count_by_role_type{key_suffix}": {
                str(role_type["role_type"]): role_type["count"]
                for role_type in roles.values("role_type").annotate(count=Count("id"))
            },
            f"count_by_role_status{key_suffix}": {
                str(role_status["status"]): role_status["count"]
                for role_status in roles.values("status").annotate(count=Count("id"))
            },
            f"count_by_accreditation_type{key_suffix}": {
                str(accreditation_type["accreditation_type"]): accreditation_type["count"]
                for accreditation_type in accreditations.values("accreditation_type").annotate(count=Count("id"))
            },
        }
