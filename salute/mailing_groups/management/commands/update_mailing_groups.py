from typing import Any

from django.core.management.base import BaseCommand
from django.db import models

from salute.hierarchy.constants import GROUP_SECTION_TYPES, SectionType
from salute.hierarchy.models import District, Group, Section
from salute.mailing_groups.models import (
    GroupSectionMailingPreferenceOption,
    GroupSectionSystemMailingPreference,
    SystemMailingGroup,
)
from salute.roles.models import RoleType, Team, TeamType

ROLES = {
    "chair": "Chair",
    "district_lead": "Lead Volunteer",
    "group_lead": "Group Lead Volunteer",
    "treasurer": "Treasurer",
    "team_leader": "Team Leader",
    "youth_lead": "Youth Lead",
}


def _get_mailing_preference(group: Group, section_type: SectionType) -> GroupSectionMailingPreferenceOption:
    """
    Get the mailing preference for a group and section type.

    If the mailing preference is not set, it defaults to teams-first.
    """
    try:
        mailing_pref_row = GroupSectionSystemMailingPreference.objects.get(group=group, section_type=section_type)
        return GroupSectionMailingPreferenceOption(mailing_pref_row.mailing_preference)
    except GroupSectionSystemMailingPreference.DoesNotExist:
        return GroupSectionMailingPreferenceOption.TEAMS


class MailingGroupUpdater:
    def __init__(self, *, district: District) -> None:
        self.district = district

        self.trustees_team_type = TeamType.objects.get(tsa_id="a4b6414e-a2f8-ed11-8f6d-6045bdd0ed08")
        self.leadership_team_type = TeamType.objects.get(tsa_id="c30f4d78-a1f8-ed11-8f6d-6045bdd0ed08")
        self.helpers_team_type = TeamType.objects.get(tsa_id="b5abf18b-a1f8-ed11-8f6d-6045bdd0ed08")
        self.fourteento24_team_type = TeamType.objects.get(tsa_id="04165cff-a0f8-ed11-8f6d-6045bdd0ed08")

    def update_district_top_level_roles(self) -> None:
        SystemMailingGroup.objects.update_or_create(
            composite_key="district_lead",
            defaults={
                "name": "lead",
                "display_name": "District Lead",
                "can_receive_external_email": True,
                "can_members_send_as": True,
                "config": {
                    "role_type_id": str(RoleType.objects.get(name=ROLES["district_lead"]).id),
                    "team_type_id": str(self.leadership_team_type.id),
                    "units": [{"type": "district", "unit_id": str(self.district.id)}],
                },
                # Fallback - not used for now
                "fallback_group_composite_key": "",
                "always_include_fallback_group": False,
            },
        )

        SystemMailingGroup.objects.update_or_create(
            composite_key="district_chair",
            defaults={
                "name": "chair",
                "display_name": "District Chair",
                "can_receive_external_email": True,
                "can_members_send_as": True,
                "config": {
                    "role_type_id": str(RoleType.objects.get(name=ROLES["chair"]).id),
                    "team_type_id": str(self.trustees_team_type.id),
                    "units": [{"type": "district", "unit_id": str(self.district.id)}],
                },
                # Fallback to Trustees
                "fallback_group_composite_key": f"district_team_{self.trustees_team_type.id}",
                "always_include_fallback_group": False,
            },
        )

        SystemMailingGroup.objects.update_or_create(
            composite_key="district_treasurer",
            defaults={
                "name": "treasurer",
                "display_name": "District Treasurer",
                "can_receive_external_email": True,
                "can_members_send_as": True,
                "config": {
                    "role_type_id": str(RoleType.objects.get(name=ROLES["treasurer"]).id),
                    "team_type_id": str(self.trustees_team_type.id),
                    "units": [{"type": "district", "unit_id": str(self.district.id)}],
                },
                # Fallback to Trustees
                "fallback_group_composite_key": f"district_team_{self.trustees_team_type.id}",
                "always_include_fallback_group": False,
            },
        )

        SystemMailingGroup.objects.update_or_create(
            composite_key="district_youth_lead",
            defaults={
                "name": "youth-lead",
                "display_name": "District Youth Lead",
                "can_receive_external_email": True,
                "can_members_send_as": True,
                "config": {
                    "role_type_id": str(RoleType.objects.get(name=ROLES["youth_lead"]).id),
                    "team_type_id": str(self.leadership_team_type.id),
                    "units": [{"type": "district", "unit_id": str(self.district.id)}],
                },
                # Fallback - not used for now
                "fallback_group_composite_key": "",
                "always_include_fallback_group": False,
            },
        )

    def update_district_teams(self) -> None:
        # First, get all teams within the district, including sub-teams.
        team_qs = Team.objects.filter(models.Q(district=self.district) | models.Q(parent_team__district=self.district))
        for team in team_qs:
            # If the team has a mailing slug, we want to create addresses for it.
            # TODO: District Wilverley Team -> Wilverley Team
            if team.team_type.mailing_slug:
                SystemMailingGroup.objects.update_or_create(
                    composite_key=f"district_team_{team.team_type.id}",
                    defaults={
                        "name": f"{team.team_type.mailing_slug}",
                        "display_name": f"District {team.team_type.display_name}",
                        "can_receive_external_email": True,
                        "can_members_send_as": team.team_type.members_can_send_as,
                        "config": {
                            "team_type_id": str(team.team_type.id),
                            "units": [{"type": "district", "unit_id": str(self.district.id)}],
                        },
                        # Fallback - not used for now
                        "fallback_group_composite_key": "",
                        "always_include_fallback_group": False,
                    },
                )

                # If the team type has a contactable team lead, create an address for them.
                if team.team_type.has_team_lead:
                    SystemMailingGroup.objects.update_or_create(
                        composite_key=f"district_team_{team.team_type.id}__lead",
                        defaults={
                            "name": f"{team.team_type.mailing_slug}-lead",
                            "display_name": f"District {team.team_type.display_name} Lead",
                            "can_receive_external_email": True,
                            "can_members_send_as": True,
                            "config": {
                                "team_type_id": str(team.team_type.id),
                                "role_type_id": str(RoleType.objects.get(name=ROLES["team_leader"]).id),
                                "units": [{"type": "district", "unit_id": str(self.district.id)}],
                            },
                            # Fallback - not used for now
                            "fallback_group_composite_key": "",
                            "always_include_fallback_group": False,
                        },
                    )

                # If the team type has an -all list, and it's not a sub-team, and it has sub-teams,
                # then create a -all list.
                if (
                    team.team_type.has_all_list
                    and team.parent_team is None
                    and team.allow_sub_team
                    and team.sub_teams.count()
                ):
                    SystemMailingGroup.objects.update_or_create(
                        composite_key=f"district_team_{team.team_type.id}__all",
                        defaults={
                            "name": f"{team.team_type.mailing_slug}-all",
                            "display_name": f"District {team.team_type.display_name} All Members",
                            "can_receive_external_email": False,
                            "can_members_send_as": False,
                            "config": {
                                "team_type_id": str(team.team_type.id),
                                "is_all_members_list": True,
                                "include_sub_teams": True,
                                "units": [{"type": "district", "unit_id": str(self.district.id)}],
                            },
                            # Fallback - not used for now
                            "fallback_group_composite_key": "",
                            "always_include_fallback_group": False,
                        },
                    )

    def update_explorer_teams(self) -> None:
        """Update teams for explorers and young leaders."""
        for district_section in self.district.sections.exclude(section_type=SectionType.NETWORK):
            if not district_section.mailing_slug:
                raise ValueError(f"Mailing slug is required for {district_section}")

            SystemMailingGroup.objects.update_or_create(
                composite_key=f"district_section_team_{district_section.tsa_id}",
                defaults={
                    "name": district_section.mailing_slug.lower(),
                    "display_name": district_section.display_name,
                    "can_receive_external_email": True,
                    "can_members_send_as": True,
                    "config": {
                        "units": [{"type": "section", "unit_id": str(district_section.id)}],
                    },
                    # Explorer units fall back to the 14-24 team lead, and should always include them.
                    "fallback_group_composite_key": f"district_team_{self.fourteento24_team_type.id}__lead",
                    "always_include_fallback_group": True,
                },
            )

    def update_network(self) -> None:
        # Iterate as we assume that there may be more than one network.
        for network_section in self.district.sections.filter(section_type=SectionType.NETWORK):
            if not network_section.mailing_slug:
                raise ValueError(f"Mailing slug is required for {network_section}")

            SystemMailingGroup.objects.update_or_create(
                composite_key=f"district_network_lead_{network_section.tsa_id}",
                defaults={
                    "name": network_section.mailing_slug.lower(),
                    "display_name": network_section.display_name,
                    "can_receive_external_email": True,
                    "can_members_send_as": True,
                    "config": {
                        "role_type_id": str(RoleType.objects.get(name=ROLES["team_leader"]).id),
                        "units": [{"type": "section", "unit_id": str(network_section.id)}],
                    },
                    # Network units fall back to the 14-24 team lead, but should not always include them.
                    "fallback_group_composite_key": f"district_team_{self.fourteento24_team_type.id}__lead",
                    "always_include_fallback_group": False,
                },
            )

            SystemMailingGroup.objects.update_or_create(
                composite_key=f"district_network_members_{network_section.tsa_id}",
                defaults={
                    "name": f"{network_section.mailing_slug.lower()}-members",
                    "display_name": f"{network_section.display_name} Members",
                    "can_receive_external_email": False,
                    "can_members_send_as": False,
                    "config": {
                        "units": [{"type": "section", "unit_id": str(network_section.id)}],
                    },
                    # Network units fall back to the 14-24 team lead, but should not always include them.
                    "fallback_group_composite_key": f"district_team_{self.fourteento24_team_type.id}__lead",
                    "always_include_fallback_group": False,
                },
            )

    def update_group_top_level_roles(self, group: Group) -> None:
        # Group Lead Volunteer
        SystemMailingGroup.objects.update_or_create(
            composite_key=f"group_lead_{group.tsa_id}",
            defaults={
                "name": f"{group.ordinal}-lead",
                "display_name": f"{group.public_name} Lead Volunteer",
                "can_receive_external_email": True,
                "can_members_send_as": True,
                "config": {
                    "role_type_id": str(RoleType.objects.get(name=ROLES["group_lead"]).id),
                    "team_type_id": str(self.leadership_team_type.id),
                    "units": [{"type": "group", "unit_id": str(group.id)}],
                },
                # Fallback - not used for now
                "fallback_group_composite_key": "",
                "always_include_fallback_group": False,
            },
        )
        # Group Chair
        SystemMailingGroup.objects.update_or_create(
            composite_key=f"group_chair_{group.tsa_id}",
            defaults={
                "name": f"{group.ordinal}-chair",
                "display_name": f"{group.public_name} Chair",
                "can_receive_external_email": True,
                "can_members_send_as": True,
                "config": {
                    "role_type_id": str(RoleType.objects.get(name=ROLES["chair"]).id),
                    "team_type_id": str(self.trustees_team_type.id),
                    "units": [{"type": "group", "unit_id": str(group.id)}],
                },
                # Group chair should fall back to the group trustees team.
                "fallback_group_composite_key": f"group_{group.tsa_id}_team_{self.trustees_team_type.id}",
            },
        )
        # Group Treasurer
        SystemMailingGroup.objects.update_or_create(
            composite_key=f"group_treasurer_{group.tsa_id}",
            defaults={
                "name": f"{group.ordinal}-treasurer",
                "display_name": f"{group.public_name} Treasurer",
                "can_receive_external_email": True,
                "can_members_send_as": True,
                "config": {
                    "role_type_id": str(RoleType.objects.get(name=ROLES["treasurer"]).id),
                    "team_type_id": str(self.trustees_team_type.id),
                    "units": [{"type": "group", "unit_id": str(group.id)}],
                },
                # Group treasurer should fall back to the group trustees team.
                "fallback_group_composite_key": f"group_{group.tsa_id}_team_{self.trustees_team_type.id}",
            },
        )

    def update_group_teams(self, group: Group) -> None:
        """
        Update Group Teams.

        This does not include section teams, so typically would only cover leadership and trustees.

        Helpers are excluded as there should be no mailing slug set.
        """
        team_qs = Team.objects.filter(models.Q(group=group) | models.Q(parent_team__group=group))
        for team in team_qs:
            if team.team_type.mailing_slug:
                SystemMailingGroup.objects.update_or_create(
                    composite_key=f"group_{group.tsa_id}_team_{team.team_type.id}",
                    defaults={
                        "name": f"{group.ordinal}-{team.team_type.mailing_slug}",
                        "display_name": f"{group.public_name} {team.team_type.display_name}",
                        "can_receive_external_email": True,
                        "can_members_send_as": team.team_type.members_can_send_as,
                        "config": {
                            "team_type_id": str(team.team_type.id),
                            "units": [{"type": "group", "unit_id": str(group.id)}],
                        },
                        # Fallback - not used for now
                        "fallback_group_composite_key": "",
                        "always_include_fallback_group": False,
                    },
                )

    def update_group_all(self, group: Group) -> None:
        # group-all - Everyone in the group or sections who is not a helper.
        SystemMailingGroup.objects.update_or_create(
            composite_key=f"group_all_{group.tsa_id}",
            defaults={
                "name": f"{group.ordinal}-all",
                "display_name": f"{group.public_name} All Members",
                "can_receive_external_email": False,
                "can_members_send_as": False,
                "config": {
                    "is_all_members_list": True,
                    "units": [{"type": "group", "unit_id": str(group.id)}]
                    + [{"type": "section", "unit_id": str(section.id)} for section in group.sections.all()],
                },
                # Fallback - not used for now
                "fallback_group_composite_key": "",
                "always_include_fallback_group": False,
            },
        )

        # All section leaders
        SystemMailingGroup.objects.update_or_create(
            composite_key=f"group_{group.tsa_id}_all_sections",
            defaults={
                "name": f"{group.ordinal}-sections",
                "display_name": f"{group.public_name} Section Teams",
                "can_receive_external_email": False,
                "can_members_send_as": False,
                "config": {
                    "units": [{"type": "section", "unit_id": str(section.id)} for section in group.sections.all()],
                },
                # Fallback - not used for now
                "fallback_group_composite_key": "",
                "always_include_fallback_group": False,
            },
        )

    def update_group_section_type(self, group: Group, section_type: SectionType) -> None:
        """
        Update mailing groups for a section type within a group.
        """
        sections = group.sections.filter(section_type=section_type)
        if sections:
            mailing_preference = _get_mailing_preference(group, section_type)

            config: dict[str, Any] = {
                "units": [{"type": "section", "unit_id": str(section.id)} for section in sections],
            }

            # Filter to just team leaders if mailing preference is leaders-first.
            if mailing_preference == GroupSectionMailingPreferenceOption.LEADERS:
                config["role_type_id"] = str(RoleType.objects.get(name=ROLES["team_leader"]).id)

            # Primary group section type mailing group, e.g 20th-cubs
            SystemMailingGroup.objects.update_or_create(
                composite_key=f"group_{group.tsa_id}_{section_type.lower()}",
                defaults={
                    "name": f"{group.ordinal}-{section_type.lower()}",
                    "display_name": f"{group.public_name} {section_type}",
                    "can_receive_external_email": True,
                    "can_members_send_as": True,
                    "config": config,
                    # Sections fall back to the group lead.
                    "fallback_group_composite_key": f"group_lead_{group.tsa_id}",
                    "always_include_fallback_group": False,
                },
            )

            # Team members mailing group, e.g 20th-cubs-team
            # Only created if mailing preference is leaders-first.
            if mailing_preference == GroupSectionMailingPreferenceOption.LEADERS:
                _, created = SystemMailingGroup.objects.update_or_create(
                    composite_key=f"group_{group.tsa_id}_{section_type.lower()}_team_members",
                    defaults={
                        "name": f"{group.ordinal}-{section_type.lower()}-team",
                        "display_name": f"{group.public_name} {section_type} Team",
                        "can_receive_external_email": False,
                        "can_members_send_as": False,
                        "config": {
                            "units": [{"type": "section", "unit_id": str(section.id)} for section in sections],
                        },
                        # Sections fall back to the group lead.
                        "fallback_group_composite_key": f"group_lead_{group.tsa_id}",
                        "always_include_fallback_group": False,
                    },
                )
                if created:
                    print(f"Created {group.public_name} {section_type} team members email.")
            else:
                # If the mailing preference is teams, then the -teams email is redundant and should not be created.
                count, _ = SystemMailingGroup.objects.filter(
                    composite_key=f"group_{group.tsa_id}_{section_type.lower()}_team_members",
                ).delete()
                if count > 0:
                    print(f"Deleted {group.public_name} {section_type} team members email.")

    def update_group_section(self, group: Group, section: Section) -> None:
        # All group sections should have a usual weekday set.
        assert section.usual_weekday is not None

        config: dict[str, Any] = {
            "units": [{"type": "section", "unit_id": str(section.id)}],
        }

        # Filter to just team leaders if mailing preference is leaders-first.
        mailing_preference = _get_mailing_preference(group, section.section_type)
        if mailing_preference == GroupSectionMailingPreferenceOption.LEADERS:
            config["role_type_id"] = str(RoleType.objects.get(name=ROLES["team_leader"]).id)

        SystemMailingGroup.objects.update_or_create(
            composite_key=f"section_team_{section.tsa_id}",
            defaults={
                "name": f"{group.ordinal}-{section.section_type}-{section.usual_weekday}".lower(),
                "display_name": f"{group.public_name} {section.usual_weekday.title()} {section.section_type}",  # noqa: E501
                "can_receive_external_email": True,
                "can_members_send_as": True,
                "config": config,
                # Sections fall back to the section team leaders at the group
                "fallback_group_composite_key": f"group_{group.tsa_id}_{section.section_type.lower()}",
                "always_include_fallback_group": False,
            },
        )


class Command(BaseCommand):
    help = "Update Mail Groups"

    def handle(self, *args: str, **options: str) -> None:
        district = District.objects.get()

        updater = MailingGroupUpdater(district=district)

        # District
        updater.update_district_top_level_roles()
        updater.update_district_teams()
        updater.update_explorer_teams()
        updater.update_network()
        # TODO: District - All Scout Leaders, Sections etc. - blocked by restricted access

        # Groups
        for group in district.groups.all():
            if group.local_unit_number is None:
                raise ValueError(f"Group local unit number is required for {group}")

            updater.update_group_top_level_roles(group)
            updater.update_group_teams(group)
            updater.update_group_all(group)

            for section_type in GROUP_SECTION_TYPES:
                updater.update_group_section_type(group, section_type)

            # Group Sections
            for section in group.sections.all():
                updater.update_group_section(group, section)

        print("Mail groups models created")
        print("Updating members")

        for mail_group in SystemMailingGroup.objects.all():
            mail_group.update_members()

        print("Done")
