import pytest
from django.db import IntegrityError

from salute.hierarchy.factories import DistrictFactory, DistrictSectionFactory, GroupFactory, GroupSectionFactory
from salute.people.factories import PersonFactory
from salute.roles.factories import (
    AccreditationFactory,
    AccreditationTypeFactory,
    DistrictSectionTeamFactory,
    DistrictSubTeamFactory,
    DistrictTeamFactory,
    GroupSectionTeamFactory,
    GroupSubTeamFactory,
    GroupTeamFactory,
    RoleFactory,
    RoleStatusFactory,
    RoleTypeFactory,
    TeamFactory,
    TeamTypeFactory,
)
from salute.roles.models import TeamType


@pytest.mark.django_db
class TestTeamType:
    def test_creation(self) -> None:
        team_type = TeamTypeFactory()
        assert team_type.pk is not None
        assert isinstance(team_type.name, str)

    def test_str(self) -> None:
        team_type = TeamTypeFactory(name="Test TeamType")
        assert str(team_type) == "Test TeamType"

    def test_str__with_nickname(self) -> None:
        team_type = TeamTypeFactory(name="Test TeamType", nickname="Bees")
        assert str(team_type) == "Bees"


@pytest.mark.django_db
class TestTeam:
    @pytest.fixture
    def team_type(self) -> TeamType:
        return TeamTypeFactory()

    def test_creation_with_district(self, team_type: TeamType) -> None:
        district = DistrictFactory()
        team = DistrictTeamFactory(district=district, team_type=team_type)
        assert team.pk is not None
        assert team.district == district
        assert team.group is None
        assert team.section is None
        assert team.parent_team is None
        assert team.team_type == team_type
        assert team.parent == district
        assert team.unit == district

    def test_creation_with_group(self, team_type: TeamType) -> None:
        group = GroupFactory()
        team = GroupTeamFactory(group=group, team_type=team_type)
        assert team.pk is not None
        assert team.district is None
        assert team.group == group
        assert team.section is None
        assert team.parent_team is None
        assert team.team_type == team_type
        assert team.parent == group
        assert team.unit == group

    def test_creation_with_group_section(self, team_type: TeamType) -> None:
        section = GroupSectionFactory()
        team = GroupSectionTeamFactory(section=section, team_type=team_type)
        assert team.pk is not None
        assert team.district is None
        assert team.group is None
        assert team.section == section
        assert team.parent_team is None
        assert team.team_type == team_type
        assert team.parent == section
        assert team.unit == section

    def test_creation_with_district_section(self, team_type: TeamType) -> None:
        section = DistrictSectionFactory()
        team = DistrictSectionTeamFactory(section=section, team_type=team_type)
        assert team.pk is not None
        assert team.district is None
        assert team.group is None
        assert team.section == section
        assert team.parent_team is None
        assert team.team_type == team_type
        assert team.parent == section
        assert team.unit == section

    def test_creation_with_parent_team__district(self, team_type: TeamType) -> None:
        district = DistrictFactory()
        parent_team = DistrictTeamFactory(district=district)
        team = DistrictSubTeamFactory(parent_team=parent_team, team_type=team_type)
        assert team.pk is not None
        assert team.parent_team == parent_team
        assert team.team_type == team_type
        assert team.parent == parent_team
        assert team.unit == district

    def test_creation_with_parent_team__group(self, team_type: TeamType) -> None:
        group = GroupFactory()
        parent_team = GroupTeamFactory(group=group)
        team = GroupSubTeamFactory(parent_team=parent_team, team_type=team_type)
        assert team.pk is not None
        assert team.parent_team == parent_team
        assert team.team_type == team_type
        assert team.parent == parent_team
        assert team.unit == group

    def test_creation_without_parent(self, team_type: TeamType) -> None:
        with pytest.raises(IntegrityError, match="CHECK constraint failed: team_only_has_one_parent_object"):
            TeamFactory(team_type=team_type)

    def test_creation_with_multiple_parents(self, team_type: TeamType) -> None:
        with pytest.raises(IntegrityError, match="CHECK constraint failed: team_only_has_one_parent_object"):
            TeamFactory(team_type=team_type, district=DistrictFactory(), group=GroupFactory())

    def test_cannot_have_multiple_teams_of_same_type_within_district(self, team_type: TeamType) -> None:
        district = DistrictFactory()
        TeamFactory(team_type=team_type, district=district)
        with pytest.raises(IntegrityError, match="UNIQUE constraint failed"):
            TeamFactory(team_type=team_type, district=district)

    def test_cannot_have_multiple_teams_of_same_type_within_group(self, team_type: TeamType) -> None:
        group = GroupFactory()
        TeamFactory(team_type=team_type, group=group)
        with pytest.raises(IntegrityError, match="UNIQUE constraint failed"):
            TeamFactory(team_type=team_type, group=group)

    def test_cannot_have_multiple_teams_of_same_type_within_section(self, team_type: TeamType) -> None:
        section = GroupSectionFactory()
        TeamFactory(team_type=team_type, section=section)
        with pytest.raises(IntegrityError, match="UNIQUE constraint failed"):
            TeamFactory(team_type=team_type, section=section)

    def test_cannot_have_multiple_subteams_of_same_type(self, team_type: TeamType) -> None:
        parent_team = DistrictTeamFactory()
        TeamFactory(team_type=team_type, parent_team=parent_team)
        with pytest.raises(IntegrityError, match="UNIQUE constraint failed"):
            TeamFactory(team_type=team_type, parent_team=parent_team)

    def test_str(self) -> None:
        team_type = TeamTypeFactory(name="Test TeamType")
        district = DistrictFactory()
        team = TeamFactory(team_type=team_type, district=district)
        assert str(team) == f"Test TeamType - {team.unit}"


@pytest.mark.django_db
class TestRoleType:
    def test_creation(self) -> None:
        role_type = RoleTypeFactory()
        assert role_type.pk is not None
        assert isinstance(role_type.name, str)

    def test_str(self) -> None:
        role_type = RoleTypeFactory(name="Test RoleType")
        assert str(role_type) == "Test RoleType"


@pytest.mark.django_db
class TestRoleStatus:
    def test_creation(self) -> None:
        role_status = RoleStatusFactory()
        assert role_status.pk is not None
        assert isinstance(role_status.name, str)

    def test_str(self) -> None:
        role_status = RoleStatusFactory(name="Test RoleStatus")
        assert str(role_status) == "Test RoleStatus"


@pytest.mark.django_db
class TestRole:
    def test_creation(self) -> None:
        person = PersonFactory()
        team = DistrictTeamFactory()
        role_type = RoleTypeFactory()
        role_status = RoleStatusFactory()
        role = RoleFactory(person=person, team=team, role_type=role_type, status=role_status)
        assert role.pk is not None
        assert role.person == person
        assert role.team == team
        assert role.role_type == role_type
        assert role.status == role_status

    def test_str(self) -> None:
        person = PersonFactory()
        team = DistrictTeamFactory()
        role_type = RoleTypeFactory(name="Test RoleType")
        role = RoleFactory(person=person, team=team, role_type=role_type)
        assert str(role) == f"{person} is {role_type.name} for {team}"


@pytest.mark.django_db
class TestAccreditationType:
    def test_creation(self) -> None:
        accreditation_type = AccreditationTypeFactory()
        assert accreditation_type.pk is not None
        assert isinstance(accreditation_type.name, str)

    def test_str(self) -> None:
        accreditation_type = AccreditationTypeFactory(name="Test AccreditationType")
        assert str(accreditation_type) == "Test AccreditationType"


@pytest.mark.django_db
class TestAccreditation:
    def test_creation(self) -> None:
        person = PersonFactory()
        team = DistrictTeamFactory()
        accreditation_type = AccreditationTypeFactory()
        accreditation = AccreditationFactory(person=person, team=team, accreditation_type=accreditation_type)
        assert accreditation.pk is not None
        assert accreditation.person == person
        assert accreditation.team == team
        assert accreditation.accreditation_type == accreditation_type

    def test_str(self) -> None:
        person = PersonFactory()
        team = DistrictTeamFactory()
        accreditation_type = AccreditationTypeFactory(name="Test AccreditationType")
        accreditation = AccreditationFactory(person=person, team=team, accreditation_type=accreditation_type)
        assert str(accreditation) == f"{accreditation_type} for {person} in {team}"
