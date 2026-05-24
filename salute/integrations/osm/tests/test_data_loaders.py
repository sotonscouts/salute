from datetime import date

import pytest
from asgiref.sync import async_to_sync

from salute.hierarchy.factories import DistrictFactory, GroupSectionFactory
from salute.integrations.osm.factories import OSMSectionHeadcountRecordFactory
from salute.integrations.osm.graphql.data_loaders import load_total_young_person_count_for_district


@pytest.mark.django_db
def test_load_total_young_person_count_for_district_uses_latest_record_per_section() -> None:
    """Older records must not be included when another section shares that date as its latest."""
    district = DistrictFactory()
    section_a = GroupSectionFactory(group__district=district)
    section_b = GroupSectionFactory(group__district=district)

    OSMSectionHeadcountRecordFactory(section=section_a, date=date(2024, 1, 1), young_person_count=5)
    OSMSectionHeadcountRecordFactory(section=section_a, date=date(2024, 1, 10), young_person_count=10)
    OSMSectionHeadcountRecordFactory(section=section_a, date=date(2024, 1, 15), young_person_count=12)

    OSMSectionHeadcountRecordFactory(section=section_b, date=date(2024, 1, 1), young_person_count=20)
    OSMSectionHeadcountRecordFactory(section=section_b, date=date(2024, 1, 10), young_person_count=8)

    result = async_to_sync(load_total_young_person_count_for_district)([(district.pk, True)])

    assert result == [20]
