import random
from random import randint

from django.conf import settings
from django.core.management.base import BaseCommand
from faker import Faker

from salute.accounts.models import User
from salute.hierarchy.constants import GROUP_SECTION_TYPES, SectionType
from salute.hierarchy.factories import DistrictFactory, DistrictSectionFactory, GroupFactory, GroupSectionFactory
from salute.hierarchy.models import District, Group
from salute.people.factories import PersonFactory
from salute.roles.factories import (
    DistrictSectionTeamFactory,
    DistrictSubTeamFactory,
    DistrictTeamFactory,
    GroupSectionTeamFactory,
    GroupSubTeamFactory,
    GroupTeamFactory,
    RoleFactory,
    RoleStatusFactory,
    RoleTypeFactory,
    TeamTypeFactory,
)
from salute.roles.models import Team, TeamType


class Command(BaseCommand):
    help = "Generate fake data for testing"

    def handle(self, *args: str, **options: str) -> None:
        if settings.DEBUG is not True:
            self.stdout.write("DEBUG is False, refusing to run.")
            return

        if District.objects.count() > 0:
            self.stdout.write("There is still data present. Please use ./manage.py flush")
            return

        # if "I am a developer and I know what I am doing" != input(
        #     "Please type `I am a developer and I know what I am doing` to begin data generation: "
        # ):
        #     return

        faker = Faker()

        # Generate a user
        User.objects.create_superuser(email="admin@example.com", password="password")  # noqa: S106
        self.stdout.write("Generated user: admin@example.com with password: `password`")

        SECTION_TEAM_TYPE_MAP: dict[SectionType, TeamType] = {  # noqa: N806
            section_type: TeamTypeFactory(name=f"{section_type.label} Section Team")
            for section_type in SectionType
            if section_type != SectionType.NETWORK
        }

        LEADERSHIP_TEAM_TYPE = TeamTypeFactory(name="Leadership Team")  # noqa: N806
        TRUSTEE_BOARD_TEAM_TYPE = TeamTypeFactory(name="Trustee Board")  # noqa: N806

        def generate_group_section(group: Group, section_type: SectionType, *, with_nicknames: bool = False) -> None:
            section = GroupSectionFactory(
                group=group,
                section_type=section_type,
                nickname=faker.word() if with_nicknames else "",
            )
            GroupSectionTeamFactory(
                section=section,
                team_type=SECTION_TEAM_TYPE_MAP[section_type],
                allow_sub_team=False,
                inherit_permissions=False,
            )

        def generate_district_section(
            district: District, section_type: SectionType, *, with_nicknames: bool = False
        ) -> None:
            section = DistrictSectionFactory(
                district=district,
                section_type=section_type,
                nickname=faker.word() if with_nicknames else "",
            )
            DistrictSectionTeamFactory(
                section=section,
                team_type=SECTION_TEAM_TYPE_MAP[section_type],
                allow_sub_team=False,
                inherit_permissions=False,
            )

        # Generate a district
        district = DistrictFactory(unit_name="Exampleton")
        DistrictTeamFactory(team_type=LEADERSHIP_TEAM_TYPE, district=district)
        DistrictTeamFactory(team_type=TRUSTEE_BOARD_TEAM_TYPE, district=district)

        for team_name, sub_teams in {
            "Programme": ("Permits", "Nights Away", "Events"),
            "Support": ("Digital", "Campsite", "Growth"),
            "Volunteer Development": ("Training", "Social", "Awards"),
        }.items():
            pt = DistrictTeamFactory(team_type__name=team_name, district=district, allow_sub_team=True)
            for st in sub_teams:
                DistrictSubTeamFactory(parent_team=pt, team_type__name=st)

        # Generate Network, Explorers and Young Leaders
        generate_district_section(district, SectionType.YOUNG_LEADERS)
        for _ in range(5):
            generate_district_section(district, SectionType.EXPLORERS, with_nicknames=True)

        # Generate 4 groups
        for _ in range(4):
            group = GroupFactory(district=district)
            GroupTeamFactory(team_type=LEADERSHIP_TEAM_TYPE, group=group)
            GroupTeamFactory(team_type=TRUSTEE_BOARD_TEAM_TYPE, group=group)

            for section_type in GROUP_SECTION_TYPES:
                generate_group_section(group, section_type)

        # Generate a super-group
        group = GroupFactory(district=district)
        super_leadership = GroupTeamFactory(team_type=LEADERSHIP_TEAM_TYPE, group=group)
        GroupTeamFactory(team_type=TRUSTEE_BOARD_TEAM_TYPE, group=group)
        GroupSubTeamFactory(parent_team=super_leadership, team_type__name="Fundraising")

        for _ in range(2):
            for section_type in GROUP_SECTION_TYPES:
                generate_group_section(group, section_type, with_nicknames=True)

        # Now generate some people, and add some roles for them.
        role_statuses = [RoleStatusFactory(name=name) for name in ("Full", "Provisional", "Provisional + System")]
        role_types = [RoleTypeFactory(name="Team Leader"), RoleTypeFactory(name="Team Member")]
        all_teams = Team.objects.all()
        people = PersonFactory.create_batch(size=250)
        for person in people:
            for _ in range(randint(1, 3)):  # noqa: S311
                RoleFactory(
                    team=random.choice(all_teams),  # noqa: S311
                    person=person,
                    status=random.choice(role_statuses),  # noqa: S311
                    role_type=random.choice(role_types),  # noqa: S311
                )
