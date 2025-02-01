from django.db import models

from salute.integrations.tsa.models import TSATimestampedObject

from .constants import DISTRICT_SECTION_TYPES, GROUP_SECTION_TYPES, GroupType, SectionType


class TSAUnit(TSATimestampedObject):
    unit_name = models.CharField(max_length=255, editable=False)
    shortcode = models.CharField(max_length=9, editable=False)  # Used for census data

    TSA_FIELDS: tuple[str, ...] = ("unit_name", "shortcode")

    class Meta:
        abstract = True

    def __str__(self) -> str:
        return self.unit_name


class District(TSAUnit):
    """Only a single instance of this model is expected."""


class Group(TSAUnit):
    # TSA Fields
    district = models.ForeignKey(District, on_delete=models.PROTECT, related_name="groups")
    group_type = models.CharField(max_length=10, choices=GroupType, editable=False)
    charity_number = models.PositiveIntegerField(null=True, editable=False)

    # Salute Fields
    local_unit_number = models.PositiveSmallIntegerField(unique=True)
    location_name = models.CharField(max_length=255)

    TSA_FIELDS = TSAUnit.TSA_FIELDS + ("district", "group_type", "charity_number")


class Section(TSAUnit):
    # TSA Fields
    district = models.ForeignKey(
        District,
        on_delete=models.PROTECT,
        related_name="sections",
        null=True,
        editable=False,
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.PROTECT,
        related_name="sections",
        null=True,
        editable=False,
    )
    section_type = models.CharField(max_length=12, choices=SectionType, editable=False)

    TSA_FIELDS = TSAUnit.TSA_FIELDS + ("district", "group", "section_type")

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(section_type__in=DISTRICT_SECTION_TYPES, district__isnull=False, group__isnull=True)
                | models.Q(section_type__in=GROUP_SECTION_TYPES, district__isnull=True, group__isnull=False),
                violation_error_message="A section must be associated with one group or district.",
                name="section_is_either_group_or_district",
            )
        ]
