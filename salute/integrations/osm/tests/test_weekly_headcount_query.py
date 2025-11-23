"""Tests for the headcount_for_sections query function."""

from datetime import date, timedelta

import pytest

from salute.hierarchy.factories import GroupSectionFactory
from salute.integrations.osm.factories import OSMSectionHeadcountRecordFactory
from salute.integrations.osm.graphql.data_loaders import headcount_for_sections
from salute.integrations.osm.graphql.graph_types import HeadcountAggregationPeriod


@pytest.mark.django_db
class TestHeadcountForSections:
    """Test the headcount_for_sections function with explicit signature."""

    def test_single_section_weekly(self) -> None:
        """Test fetching weekly data for a single section."""
        section = GroupSectionFactory()
        base_date = date(2024, 1, 1)

        OSMSectionHeadcountRecordFactory(section=section, date=base_date, young_person_count=20)
        OSMSectionHeadcountRecordFactory(section=section, date=base_date + timedelta(days=2), young_person_count=22)

        result = headcount_for_sections(
            section_ids=[section.id],
            start_date=None,
            end_date=None,
            period=HeadcountAggregationPeriod.WEEK,
        )

        assert section.id in result
        assert len(result[section.id]) == 1  # One week
        assert result[section.id][0]["young_person_count"] == 22  # Max in week

    def test_multiple_sections(self) -> None:
        """Test fetching data for multiple sections in a single query."""
        section1 = GroupSectionFactory()
        section2 = GroupSectionFactory()
        base_date = date(2024, 1, 1)

        OSMSectionHeadcountRecordFactory(section=section1, date=base_date, young_person_count=20)
        OSMSectionHeadcountRecordFactory(section=section2, date=base_date, young_person_count=30)

        result = headcount_for_sections(
            section_ids=[section1.id, section2.id],
            start_date=None,
            end_date=None,
            period=HeadcountAggregationPeriod.WEEK,
        )

        assert section1.id in result
        assert section2.id in result
        assert result[section1.id][0]["young_person_count"] == 20
        assert result[section2.id][0]["young_person_count"] == 30

    def test_with_date_filters(self) -> None:
        """Test that date filters are applied correctly."""
        section = GroupSectionFactory()

        # Create records in January, February, and March
        OSMSectionHeadcountRecordFactory(section=section, date=date(2024, 1, 15), young_person_count=20)
        OSMSectionHeadcountRecordFactory(section=section, date=date(2024, 2, 15), young_person_count=25)
        OSMSectionHeadcountRecordFactory(section=section, date=date(2024, 3, 15), young_person_count=22)

        # Query only February
        result = headcount_for_sections(
            section_ids=[section.id],
            start_date=date(2024, 2, 1),
            end_date=date(2024, 2, 29),
            period=HeadcountAggregationPeriod.WEEK,
        )

        assert len(result[section.id]) == 1
        assert result[section.id][0]["young_person_count"] == 25

    def test_empty_sections_list(self) -> None:
        """Test with empty section list."""
        result = headcount_for_sections(
            section_ids=[],
            start_date=None,
            end_date=None,
            period=HeadcountAggregationPeriod.WEEK,
        )

        assert result == {}

    def test_section_with_no_data(self) -> None:
        """Test section that has no headcount records."""
        section = GroupSectionFactory()

        result = headcount_for_sections(
            section_ids=[section.id],
            start_date=None,
            end_date=None,
            period=HeadcountAggregationPeriod.WEEK,
        )

        assert section.id in result
        assert result[section.id] == []

    def test_aggregation_by_day(self) -> None:
        """Test that records are returned by day without aggregation."""
        section = GroupSectionFactory()

        # Create records on different days
        OSMSectionHeadcountRecordFactory(section=section, date=date(2024, 1, 1), young_person_count=20)
        OSMSectionHeadcountRecordFactory(section=section, date=date(2024, 1, 2), young_person_count=25)
        OSMSectionHeadcountRecordFactory(section=section, date=date(2024, 1, 3), young_person_count=22)

        result = headcount_for_sections(
            section_ids=[section.id],
            start_date=None,
            end_date=None,
            period=HeadcountAggregationPeriod.DAY,
        )

        # Should have three separate days
        assert len(result[section.id]) == 3
        assert result[section.id][0]["young_person_count"] == 20
        assert result[section.id][1]["young_person_count"] == 25
        assert result[section.id][2]["young_person_count"] == 22

    def test_aggregation_by_week(self) -> None:
        """Test that records are correctly aggregated by week with max values."""
        section = GroupSectionFactory()
        monday = date(2024, 1, 1)  # A Monday

        # Create multiple records in the same week
        OSMSectionHeadcountRecordFactory(section=section, date=monday, young_person_count=20)
        OSMSectionHeadcountRecordFactory(section=section, date=monday + timedelta(days=1), young_person_count=25)
        OSMSectionHeadcountRecordFactory(section=section, date=monday + timedelta(days=3), young_person_count=22)

        result = headcount_for_sections(
            section_ids=[section.id],
            start_date=None,
            end_date=None,
            period=HeadcountAggregationPeriod.WEEK,
        )

        # Should have one week with max values
        assert len(result[section.id]) == 1
        assert result[section.id][0]["young_person_count"] == 25  # Maximum

    def test_aggregation_by_month(self) -> None:
        """Test that records are correctly aggregated by month with max values."""
        section = GroupSectionFactory()

        # Create records in January and February
        OSMSectionHeadcountRecordFactory(section=section, date=date(2024, 1, 5), young_person_count=20)
        OSMSectionHeadcountRecordFactory(section=section, date=date(2024, 1, 15), young_person_count=25)
        OSMSectionHeadcountRecordFactory(section=section, date=date(2024, 2, 10), young_person_count=22)

        result = headcount_for_sections(
            section_ids=[section.id],
            start_date=None,
            end_date=None,
            period=HeadcountAggregationPeriod.MONTH,
        )

        # Should have two months
        assert len(result[section.id]) == 2
        assert result[section.id][0]["young_person_count"] == 25  # Max in January
        assert result[section.id][1]["young_person_count"] == 22  # Max in February

    def test_aggregation_by_year(self) -> None:
        """Test that records are correctly aggregated by year with max values."""
        section = GroupSectionFactory()

        # Create records across 2023 and 2024
        OSMSectionHeadcountRecordFactory(section=section, date=date(2023, 6, 15), young_person_count=20)
        OSMSectionHeadcountRecordFactory(section=section, date=date(2023, 12, 10), young_person_count=25)
        OSMSectionHeadcountRecordFactory(section=section, date=date(2024, 3, 5), young_person_count=22)

        result = headcount_for_sections(
            section_ids=[section.id],
            start_date=None,
            end_date=None,
            period=HeadcountAggregationPeriod.YEAR,
        )

        # Should have two years
        assert len(result[section.id]) == 2
        assert result[section.id][0]["young_person_count"] == 25  # Max in 2023
        assert result[section.id][1]["young_person_count"] == 22  # Max in 2024
