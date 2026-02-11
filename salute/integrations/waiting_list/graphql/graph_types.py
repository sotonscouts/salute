"""GraphQL types for OSM integration."""

from __future__ import annotations

from datetime import date
from enum import Enum

import strawberry as sb


@sb.enum
class HeadcountAggregationPeriod(Enum):
    """The period over which to aggregate headcount data."""

    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"


@sb.type
class HeadcountDataPoint:
    """Represents an aggregated headcount data point."""

    period_start: date = sb.field(description="The start date of the aggregation period")
    young_person_count: int = sb.field(description="The maximum young person count for that period")
