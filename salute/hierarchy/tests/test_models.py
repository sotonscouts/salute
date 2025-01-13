import pytest
from django.db.utils import IntegrityError

from salute.hierarchy.constants import SectionType
from salute.hierarchy.factories import (
    DistrictFactory,
    DistrictSectionFactory,
    GroupFactory,
    GroupSectionFactory,
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
        group = GroupFactory(district=district)
        assert Group.objects.count() == 1
        assert group.district == district
        assert group.local_unit_number > 0
        assert group.charity_number >= 100000

    def test_unique_local_unit_number(self) -> None:
        district = DistrictFactory()
        GroupFactory(district=district, local_unit_number=1)
        with pytest.raises(IntegrityError):
            GroupFactory(district=district, local_unit_number=1)  # Duplicate local unit number


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
