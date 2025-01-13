from django.db import models


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
    NETWORK = "Network"


DISTRICT_SECTION_TYPES = {SectionType.EXPLORERS, SectionType.NETWORK}
GROUP_SECTION_TYPES = set(SectionType) - DISTRICT_SECTION_TYPES
