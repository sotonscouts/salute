from decimal import Decimal

import strawberry as sb


@sb.type
class SectionCensusReturn:
    year: int
    annual_subs_cost: Decimal
    total_volunteers: int
    total_young_people: int
    ratio_young_people_to_volunteers: Decimal
