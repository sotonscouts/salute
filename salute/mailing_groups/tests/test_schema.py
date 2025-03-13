import pytest

from salute.mailing_groups.schema import MailGroupConfig
from salute.roles.factories import (
    DistrictTeamFactory,
    GroupSectionTeamFactory,
    GroupTeamFactory,
    RoleFactory,
    RoleTypeFactory,
    TeamTypeFactory,
)


@pytest.mark.django_db
class TestRoleAliasSchema:
    def test_team_type_or_team_not_found(self) -> None:
        role_type = RoleTypeFactory(name="Lead Volunteer")
        config = MailGroupConfig.model_validate(
            {
                "role_type_id": role_type.id,
                "team_type_id": "00000000-0000-0000-0000-000000000000",
                "unit": {"type": "district", "unit_id": "00000000-0000-0000-0000-000000000000"},
            }
        )
        assert config.get_members().count() == 0

    def test_role_type_unknown(self) -> None:
        leadership_team = DistrictTeamFactory(team_type__name="Leadership Team")
        config = MailGroupConfig.model_validate(
            {
                "role_type_id": "00000000-0000-0000-0000-000000000000",
                "team_type_id": leadership_team.team_type.id,
                "unit": {"type": "district", "unit_id": leadership_team.district.id},
            }
        )
        assert config.get_members().count() == 0

    def test_district_role__one_member(self) -> None:
        leadership_team = DistrictTeamFactory(team_type__name="Leadership Team")
        role_type = RoleTypeFactory(name="Lead Volunteer")
        role = RoleFactory(team=leadership_team, role_type=role_type)

        config = MailGroupConfig.model_validate(
            {
                "role_type_id": role_type.id,
                "team_type_id": leadership_team.team_type.id,
                "unit": {"type": "district", "unit_id": leadership_team.district.id},
            }
        )

        assert list(config.get_members()) == [role.person]

    def test_district_role__two_members(self) -> None:
        leadership_team = DistrictTeamFactory(team_type__name="Leadership Team")
        role_type = RoleTypeFactory(name="Lead Volunteer")
        role = RoleFactory(team=leadership_team, role_type=role_type)
        role2 = RoleFactory(team=leadership_team, role_type=role_type)

        config = MailGroupConfig.model_validate(
            {
                "role_type_id": role_type.id,
                "team_type_id": leadership_team.team_type.id,
                "unit": {"type": "district", "unit_id": leadership_team.district.id},
            }
        )

        assert set(config.get_members()) == {role.person, role2.person}

    def test_district_role__no_members(self) -> None:
        leadership_team = DistrictTeamFactory(team_type__name="Leadership Team")
        role_type = RoleTypeFactory(name="Lead Volunteer")

        config = MailGroupConfig.model_validate(
            {
                "role_type_id": role_type.id,
                "team_type_id": leadership_team.team_type.id,
                "unit": {"type": "district", "unit_id": leadership_team.district.id},
            }
        )

        assert set(config.get_members()) == set()

    def test_group_role__one_member(self) -> None:
        leadership_team = GroupTeamFactory(team_type__name="Leadership Team")
        role_type = RoleTypeFactory(name="Group Lead Volunteer")
        role = RoleFactory(team=leadership_team, role_type=role_type)

        config = MailGroupConfig.model_validate(
            {
                "role_type_id": role_type.id,
                "team_type_id": leadership_team.team_type.id,
                "unit": {"type": "group", "unit_id": leadership_team.group.id},
            }
        )

        assert list(config.get_members()) == [role.person]

    def test_group_role__two_members(self) -> None:
        section_team = GroupTeamFactory(team_type__name="Leadership Team")
        role_type = RoleTypeFactory(name="Group Lead Volunteer")
        role = RoleFactory(team=section_team, role_type=role_type)
        role2 = RoleFactory(team=section_team, role_type=role_type)

        config = MailGroupConfig.model_validate(
            {
                "role_type_id": role_type.id,
                "team_type_id": section_team.team_type.id,
                "unit": {"type": "group", "unit_id": section_team.group.id},
            }
        )

        assert set(config.get_members()) == {role.person, role2.person}

    def test_group_role__no_members(self) -> None:
        section_team = GroupTeamFactory(team_type__name="Leadership Team")
        role_type = RoleTypeFactory(name="Group Lead Volunteer")

        config = MailGroupConfig.model_validate(
            {
                "role_type_id": role_type.id,
                "team_type_id": section_team.team_type.id,
                "unit": {"type": "group", "unit_id": section_team.group.id},
            }
        )

        assert set(config.get_members()) == set()

    def test_section_role__one_member(self) -> None:
        section_team = GroupSectionTeamFactory(team_type__name="Scout Section Team")
        role_type = RoleTypeFactory(name="Team Leader")
        role = RoleFactory(team=section_team, role_type=role_type)

        config = MailGroupConfig.model_validate(
            {
                "role_type_id": role_type.id,
                "team_type_id": section_team.team_type.id,
                "unit": {"type": "section", "unit_id": section_team.section.id},
            }
        )

        assert list(config.get_members()) == [role.person]


@pytest.mark.django_db
class TestAllOfRoleSchema:
    def test_all_group_leads(self) -> None:
        role_type = RoleTypeFactory(name="Group Lead Volunteer")
        team_type = TeamTypeFactory(name="Leadership Team")
        roles = RoleFactory.create_batch(size=10, role_type=role_type, team__team_type=team_type)

        # Let's be extra annoying, and add a duplicate role for one person in another group
        RoleFactory(role_type=role_type, team__team_type=team_type, person=roles[0].person)

        # Random role that is not a Group Lead
        RoleFactory()

        config = MailGroupConfig.model_validate(
            {
                "role_type_id": role_type.id,
                "team_type_id": team_type.id,
            }
        )

        members = config.get_members()
        assert members.count() == 10
        assert set(members) == {role.person for role in roles}

    def test_all_chairs(self) -> None:
        role_type = RoleTypeFactory(name="Chair")
        roles = RoleFactory.create_batch(size=10, role_type=role_type)

        # Let's be extra annoying, and add a duplicate role for one person
        RoleFactory(role_type=role_type, person=roles[0].person)

        # Random role that is not a Chair
        RoleFactory()

        config = MailGroupConfig.model_validate(
            {
                "role_type_id": role_type.id,
            }
        )

        members = config.get_members()
        assert members.count() == 10
        assert set(members) == {role.person for role in roles}
