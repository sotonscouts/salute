from typing import TypedDict

from django.db import models


class Weekday(models.TextChoices):
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"


class GroupType(models.TextChoices):
    AIR = "Air"
    LAND = "Land"
    SEA = "Sea"


class SectionType(models.TextChoices):
    SQUIRRELS = "Squirrels"
    BEAVERS = "Beavers"
    CUBS = "Cubs"
    SCOUTS = "Scouts"
    EXPLORERS = "Explorers"
    YOUNG_LEADERS = "Young Leader"
    NETWORK = "Network"


class SectionOperatingCategory(models.TextChoices):
    DISTRICT = "district"
    GROUP = "group"


class SectionTypeInfoDict(TypedDict):
    display_name: str
    operating_category: SectionOperatingCategory
    min_age: str
    max_age: str


SECTION_TYPE_INFO: dict[SectionType, SectionTypeInfoDict] = {
    SectionType.SQUIRRELS: {
        "display_name": "Squirrels",
        "operating_category": SectionOperatingCategory.GROUP,
        "min_age": "4",
        "max_age": "5",
    },
    SectionType.BEAVERS: {
        "display_name": "Beavers",
        "operating_category": SectionOperatingCategory.GROUP,
        "min_age": "6",
        "max_age": "8",
    },
    SectionType.CUBS: {
        "display_name": "Cubs",
        "operating_category": SectionOperatingCategory.GROUP,
        "min_age": "8",
        "max_age": "10½",
    },
    SectionType.SCOUTS: {
        "display_name": "Scouts",
        "operating_category": SectionOperatingCategory.GROUP,
        "min_age": "10½",
        "max_age": "14",
    },
    SectionType.EXPLORERS: {
        "display_name": "Explorers",
        "operating_category": SectionOperatingCategory.DISTRICT,
        "min_age": "14",
        "max_age": "18",
    },
    SectionType.YOUNG_LEADERS: {
        "display_name": "Young Leaders",
        "operating_category": SectionOperatingCategory.DISTRICT,
        "min_age": "14",
        "max_age": "18",
    },
    SectionType.NETWORK: {
        "display_name": "Network",
        "operating_category": SectionOperatingCategory.DISTRICT,
        "min_age": "18",
        "max_age": "25",
    },
}


DISTRICT_SECTION_TYPES = [
    st for st, info in SECTION_TYPE_INFO.items() if info["operating_category"] == SectionOperatingCategory.DISTRICT
]
GROUP_SECTION_TYPES = [
    st for st, info in SECTION_TYPE_INFO.items() if info["operating_category"] == SectionOperatingCategory.GROUP
]

# Section types that do not necessarily meet on a regular weekday
NON_REGULAR_SECTIONS_TYPES = [SectionType.YOUNG_LEADERS, SectionType.NETWORK]
