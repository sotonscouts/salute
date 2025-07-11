import pytest

from salute.accounts.factories import UserFactory
from salute.accounts.models import DistrictUserRole, DistrictUserRoleType, User
from salute.hierarchy.factories import DistrictFactory
from salute.people.factories import PersonFactory
from salute.people.models import Person


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
            primary_email="primary@example.com",
            default_email="default@example.com",
            alternate_email="alternate@example.com",
        )
        assert person.tsa_email == "primary@example.com"

        person_without_primary_email = PersonFactory(
            primary_email="", default_email="default@example.com", alternate_email="alternate@example.com"
        )
        assert person_without_primary_email.tsa_email == "default@example.com"

        person_without_primary_and_default_email = PersonFactory(
            primary_email="", default_email="", alternate_email="alternate@example.com"
        )
        assert person_without_primary_and_default_email.tsa_email == "alternate@example.com"

        person_without_any_email = PersonFactory(primary_email="", default_email="", alternate_email="")
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
