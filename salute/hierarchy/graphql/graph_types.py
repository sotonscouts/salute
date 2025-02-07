from __future__ import annotations

import strawberry as sb

from salute.hierarchy.constants import SectionOperatingCategory, SectionType


@sb.type
class SectionTypeInfo:
    value: SectionType = sb.field()
    display_name: str
    operating_category: SectionOperatingCategory

    # Hide the min and max age from the API for now
    min_age: sb.Private[str]
    max_age: sb.Private[str]

    @sb.field
    def formatted_age_range(self) -> str:
        return f"{self.min_age} - {self.max_age} years"
