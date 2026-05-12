import pytest

from salute.accounts.factories import UserFactory
from salute.accounts.models import DistrictUserRole, DistrictUserRoleType, User
from salute.hierarchy.constants import SectionType
from salute.hierarchy.factories import DistrictFactory, GroupFactory, GroupSectionFactory
from salute.hierarchy.models import Group
from salute.people.factories import PersonFactory
from salute.people.models import Person
from salute.roles.factories import (
    DistrictTeamFactory,
    GroupSectionTeamFactory,
    GroupSubTeamFactory,
    GroupTeamFactory,
    RoleFactory,
    TeamTypeFactory,
)


@pytest.mark.django_db
class TestPersonModel:
    def test_person_str(self) -> None:
        person = PersonFactory()
        expected_str = f"{person.display_name} ({person.formatted_membership_number})"
        assert str(person) == expected_str

    def test_formatted_membership_number(self) -> None:
        person = PersonFactory(membership_number=123)
        assert person.formatted_membership_number == "0000000123"

    def test_generated_first_name(self) -> None:
        person = PersonFactory(preferred_name="John", legal_name="Jonathan")
        assert person.first_name == "John"

        person_without_preferred_name = PersonFactory(preferred_name="", legal_name="Jonathan")
        assert person_without_preferred_name.first_name == "Jonathan"

    def test_generated_display_name(self) -> None:
        person = PersonFactory(preferred_name="John", last_name="Doe")
        assert person.display_name == "John Doe"

        person_without_preferred_name = PersonFactory(preferred_name="", legal_name="Jonathan", last_name="Doe")
        assert person_without_preferred_name.display_name == "Jonathan Doe"

    def test_generated_tsa_email(self) -> None:
        person = PersonFactory(
            default_email="default@example.com",
            alternate_email="alternate@example.com",
        )
        assert person.tsa_email == "alternate@example.com"

        person_without_default_email = PersonFactory(default_email="", alternate_email="alternate@example.com")
        assert person_without_default_email.tsa_email == "alternate@example.com"

        person_without_alternate_email = PersonFactory(default_email="default@example.com", alternate_email="")
        assert person_without_alternate_email.tsa_email == "default@example.com"

        person_without_any_email = PersonFactory(default_email="", alternate_email="")
        assert person_without_any_email.tsa_email is None


@pytest.mark.django_db
class TestPersonQueryset:
    @pytest.fixture
    def user(self) -> User:
        return UserFactory()

    def test_for_user__no_person(self, user: User) -> None:
        _ = PersonFactory.create_batch(5)
        assert Person.objects.for_user(user).count() == 0

    def test_for_user__get_self(self, user: User) -> None:
        people = PersonFactory.create_batch(5)
        user.person = people[2]
        user.save()

        person_ids = list(Person.objects.for_user(user).values_list("id", flat=True))

        assert person_ids == [people[2].id]

    @pytest.mark.parametrize("district_role", DistrictUserRoleType)
    def test_for_user__district_role(self, user: User, district_role: DistrictUserRoleType) -> None:
        district = DistrictFactory()
        DistrictUserRole.objects.create(user=user, district=district, level=district_role)
        _ = PersonFactory.create_batch(5)
        assert Person.objects.for_user(user).count() == 5

    @pytest.mark.parametrize("district_role", DistrictUserRoleType)
    def test_for_user__district_role_with_person(self, user: User, district_role: DistrictUserRoleType) -> None:
        district = DistrictFactory()
        DistrictUserRole.objects.create(user=user, district=district, level=district_role)
        people = PersonFactory.create_batch(5)
        user.person = people[2]
        user.save()

        assert Person.objects.for_user(user).count() == 5


@pytest.mark.django_db
class TestPersonQuerysetHasRoleInGroup:
    """Cover `PersonQuerySet.has_role_in_group` for group teams, group sub-teams, and section teams."""

    @pytest.fixture
    def fourteenth_group(self) -> Group:
        return GroupFactory(unit_name="14th Example Scouts")

    @staticmethod
    def _has_role_flag(person: Person, groups: list[Group]) -> bool:
        annotated = Person.objects.filter(pk=person.pk).has_role_in_group(groups).get()
        return bool(annotated.has_role_in_group)

    def test_has_role_in_group__leadership_team(self, fourteenth_group: Group) -> None:
        """Role on the 14th group leadership team (direct `team.group`)."""
        person = PersonFactory()
        leadership_type = TeamTypeFactory(name="Leadership Team")
        team = GroupTeamFactory(group=fourteenth_group, team_type=leadership_type)
        RoleFactory(person=person, team=team)

        assert self._has_role_flag(person, [fourteenth_group]) is True

    def test_has_role_in_group__trustee_board_fundraising_sub_team(self, fourteenth_group: Group) -> None:
        """Role on a sub-team under a group team (`team.parent_team.group`)."""
        person = PersonFactory()
        trustee_board_type = TeamTypeFactory(name="Trustee Board")
        fundraising_type = TeamTypeFactory(name="Fundraising Sub Team")
        parent = GroupTeamFactory(group=fourteenth_group, team_type=trustee_board_type)
        sub_team = GroupSubTeamFactory(parent_team=parent, team_type=fundraising_type)
        RoleFactory(person=person, team=sub_team)

        assert self._has_role_flag(person, [fourteenth_group]) is True

    def test_has_role_in_group__cubs_section_team(self, fourteenth_group: Group) -> None:
        """Role on the 14th Cubs section team (`team.section.group`)."""
        person = PersonFactory()
        section = GroupSectionFactory(group=fourteenth_group, section_type=SectionType.CUBS)
        cubs_team_type = TeamTypeFactory(name="Cubs Section Team")
        team = GroupSectionTeamFactory(section=section, team_type=cubs_team_type)
        RoleFactory(person=person, team=team)

        assert self._has_role_flag(person, [fourteenth_group]) is True

    def test_has_role_in_group__false_when_role_in_other_group(self, fourteenth_group: Group) -> None:
        other_group = GroupFactory(unit_name="99th Elsewhere")
        person = PersonFactory()
        RoleFactory(person=person, team=GroupTeamFactory(group=other_group))

        assert self._has_role_flag(person, [fourteenth_group]) is False

    def test_has_role_in_group__false_when_only_district_team(self, fourteenth_group: Group) -> None:
        person = PersonFactory()
        RoleFactory(person=person, team=DistrictTeamFactory())

        assert self._has_role_flag(person, [fourteenth_group]) is False

    def test_has_role_in_group__false_when_no_roles(self, fourteenth_group: Group) -> None:
        person = PersonFactory()

        assert self._has_role_flag(person, [fourteenth_group]) is False
