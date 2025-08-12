from decimal import Decimal

import pytest

from salute.hierarchy.factories import DistrictSectionFactory
from salute.stats.models import SectionCensusDataFormatVersion, SectionCensusReturn


@pytest.mark.django_db
class TestSectionCensusReturn:
    def test_no_data(self) -> None:
        section = DistrictSectionFactory()
        SectionCensusReturn.objects.create(
            section=section,
            data_format_version=SectionCensusDataFormatVersion.V1,
            year=2020,
            data={},
        )
        census_return = section.census_returns.first()
        assert census_return.annual_subs_cost is None
        assert census_return.total_volunteers == 0
        assert census_return.total_young_people == 0
        assert census_return.ratio_young_people_to_volunteers == Decimal("0.00")

    def test_annual_subs_cost(self) -> None:
        section = DistrictSectionFactory()
        SectionCensusReturn.objects.create(
            section=section,
            data_format_version=SectionCensusDataFormatVersion.V1,
            year=2020,
            data={
                "annual_cost": "100",
            },
        )
        assert section.census_returns.first().annual_subs_cost == Decimal("100.00")

    def test_generated_fields(self) -> None:
        section = DistrictSectionFactory()
        SectionCensusReturn.objects.create(
            section=section,
            data_format_version=SectionCensusDataFormatVersion.V1,
            year=2020,
            data={
                "y_4_m": "4",
                "y_4_f": "2",
                "y_4_p": "1",
                "y_4_s": "1",
                "y_5_m": "1",
                "y_5_f": "3",
                "y_5_p": "1",
                "y_5_s": "1",
                "l_asl_m": "3",
                "l_sl_f": "4",
            },
        )
        census_return = section.census_returns.first()
        assert census_return.total_volunteers == 7
        assert census_return.total_young_people == 14
        assert census_return.ratio_young_people_to_volunteers == Decimal("2.00")
