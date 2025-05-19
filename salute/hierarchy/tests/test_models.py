import pytest
from django.db.utils import IntegrityError

from salute.hierarchy.constants import SectionType
from salute.hierarchy.factories import (
    DistrictFactory,
    DistrictSectionFactory,
    GroupFactory,
    GroupSectionFactory,
    LocalityFactory,
)
from salute.hierarchy.models import District, Group, Section


@pytest.mark.django_db
class TestDistrictModel:
    def test_create_district(self) -> None:
        district = DistrictFactory()
        assert District.objects.count() == 1
        assert district.unit_name is not None
        assert district.shortcode is not None


@pytest.mark.django_db
class TestGroupModel:
    def test_create_group(self) -> None:
        district = DistrictFactory()
        group = GroupFactory(district=district, local_unit_number=45, locality__name="Exampleton")
        assert Group.objects.count() == 1
        assert group.district == district
        assert group.local_unit_number > 0
        assert group.charity_number >= 100000

        assert group.display_name == f"45th ({group.location_name})"
        assert group.public_name == f"45th Exampleton ({group.location_name})"

    def test_unique_local_unit_number(self) -> None:
        district = DistrictFactory()
        locality = LocalityFactory()
        GroupFactory(district=district, local_unit_number=1, locality=locality)
        with pytest.raises(IntegrityError):
            GroupFactory(district=district, local_unit_number=1, locality=locality)  # Duplicate local unit number

    def test_unique_local_unit_number__separate_localities(self) -> None:
        district = DistrictFactory()
        GroupFactory(district=district, local_unit_number=1, locality__name="Exampleton")
        GroupFactory(district=district, local_unit_number=1, locality__name="Exampleville")  # Different localities

    def test_ordinal(self) -> None:
        district = DistrictFactory()
        assert GroupFactory(district=district, local_unit_number=1).ordinal == "1st"
        assert GroupFactory(district=district, local_unit_number=2).ordinal == "2nd"
        assert GroupFactory(district=district, local_unit_number=3).ordinal == "3rd"
        assert GroupFactory(district=district, local_unit_number=4).ordinal == "4th"
        assert GroupFactory(district=district, local_unit_number=10).ordinal == "10th"
        assert GroupFactory(district=district, local_unit_number=11).ordinal == "11th"
        assert GroupFactory(district=district, local_unit_number=12).ordinal == "12th"
        assert GroupFactory(district=district, local_unit_number=21).ordinal == "21st"


@pytest.mark.django_db
class TestSectionModel:
    def test_create_section_with_district(self) -> None:
        district = DistrictFactory()
        section = DistrictSectionFactory(
            district=district,
            group=None,
            section_type=SectionType.EXPLORERS,
        )
        assert Section.objects.count() == 1
        assert section.district == district
        assert section.group is None

    def test_create_section_with_group(self) -> None:
        group = GroupFactory()
        section = GroupSectionFactory(
            district=None,
            group=group,
            section_type=SectionType.BEAVERS,
        )
        assert Section.objects.count() == 1
        assert section.group == group
        assert section.district is None

    def test_check_constraint_district_association(self) -> None:
        """A section with a district type must have a district or group."""
        with pytest.raises(IntegrityError, match="section_is_either_group_or_district"):
            DistrictSectionFactory(
                district=None,
                group=None,
                section_type=SectionType.EXPLORERS,
            )

    def test_check_constraint_invalid_case(self) -> None:
        """A section cannot have both a group and a district."""
        district = DistrictFactory()
        group = GroupFactory(district=district)
        with pytest.raises(IntegrityError, match="section_is_either_group_or_district"):
            GroupSectionFactory(
                district=district,
                group=group,
                section_type=SectionType.BEAVERS,
            )

    def test_check_constraint_missing_weekday(self) -> None:
        """A section must have a weekday, unless it is network or young leaders."""
        with pytest.raises(IntegrityError, match="regular_sections_must_have_usual_weekday"):
            GroupSectionFactory(
                usual_weekday=None,
            )

    def test_check_constraint_missing_weekday_allowed(self) -> None:
        """A section must have a weekday, unless it is network or young leaders."""
        DistrictSectionFactory(
            usual_weekday=None,
            section_type=SectionType.YOUNG_LEADERS,
        )
        DistrictSectionFactory(
            usual_weekday=None,
            section_type=SectionType.NETWORK,
        )

    def test_check_constraint_explorers_require_nickname(self) -> None:
        """An explorer unit must have a nickname."""
        with pytest.raises(IntegrityError, match="explorers_must_have_nickname"):
            DistrictSectionFactory(
                usual_weekday="tuesday",
                section_type=SectionType.EXPLORERS,
                nickname="",
            )

    def test_display_name_group_section(self) -> None:
        section = GroupSectionFactory(usual_weekday="tuesday", section_type="Beavers", group__local_unit_number=13)
        assert section.display_name == "13th Beavers (Tuesday)"

    def test_display_name_group_section_with_nickname(self) -> None:
        section = GroupSectionFactory(
            usual_weekday="tuesday", nickname="Wolves", section_type="Scouts", group__local_unit_number=13
        )
        assert section.display_name == "13th Scouts (Wolves)"

    def test_display_name_district_section(self) -> None:
        district = DistrictFactory(unit_name="Exampleton")

        # Network no nickname
        network = DistrictSectionFactory(
            section_type=SectionType.NETWORK,
            nickname="",
            district=district,
        )
        assert network.display_name == "Exampleton Network"

        # Network with nickname
        network = DistrictSectionFactory(
            section_type=SectionType.NETWORK,
            nickname="Hive",
            district=district,
        )
        assert network.display_name == "Hive Network"

        # Young Leaders no nickname
        network = DistrictSectionFactory(
            section_type=SectionType.YOUNG_LEADERS,
            nickname="",
            district=district,
        )
        assert network.display_name == "Exampleton Young Leaders"

        # Young Leaders with nickname
        network = DistrictSectionFactory(
            section_type=SectionType.YOUNG_LEADERS,
            nickname="Hive",
            district=district,
        )
        assert network.display_name == "Hive Young Leaders"
