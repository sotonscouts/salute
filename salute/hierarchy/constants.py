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


DISTRICT_SECTION_TYPES = [SectionType.EXPLORERS, SectionType.YOUNG_LEADERS, SectionType.NETWORK]
GROUP_SECTION_TYPES = [SectionType.SQUIRRELS, SectionType.BEAVERS, SectionType.CUBS, SectionType.SCOUTS]

# Section types that do not necessarily meet on a regular weekday
NON_REGULAR_SECTIONS_TYPES = [SectionType.YOUNG_LEADERS, SectionType.NETWORK]
