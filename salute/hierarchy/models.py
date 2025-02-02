from django.db import models
from django_choices_field import TextChoicesField

from salute.hierarchy.utils import get_ordinal_suffix
from salute.integrations.tsa.models import TSATimestampedObject

from .constants import (
    DISTRICT_SECTION_TYPES,
    GROUP_SECTION_TYPES,
    NON_REGULAR_SECTIONS_TYPES,
    GroupType,
    SectionType,
    Weekday,
)


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

    @property
    def display_name(self) -> str:
        return self.unit_name


class Group(TSAUnit):
    # TSA Fields
    district = models.ForeignKey(District, on_delete=models.PROTECT, related_name="groups")
    group_type = TextChoicesField(choices_enum=GroupType, editable=False)
    charity_number = models.PositiveIntegerField(null=True, editable=False)

    # Salute Fields
    local_unit_number = models.PositiveSmallIntegerField(unique=True)
    location_name = models.CharField(max_length=255)

    @property
    def ordinal(self) -> str:
        suffix = get_ordinal_suffix(self.local_unit_number)
        return f"{self.local_unit_number}{suffix}"

    @property
    def display_name(self) -> str:
        return f"{self.ordinal} ({self.location_name})"

    TSA_FIELDS = TSAUnit.TSA_FIELDS + ("district", "group_type", "charity_number")

    def __str__(self) -> str:
        return self.display_name


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
    section_type = TextChoicesField(choices_enum=SectionType, editable=False)

    # Salute fields
    nickname = models.CharField(max_length=32, blank=True)
    usual_weekday = TextChoicesField(choices_enum=Weekday, null=True)

    TSA_FIELDS = TSAUnit.TSA_FIELDS + ("district", "group", "section_type")

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(section_type__in=DISTRICT_SECTION_TYPES, district__isnull=False, group__isnull=True)
                | models.Q(section_type__in=GROUP_SECTION_TYPES, district__isnull=True, group__isnull=False),
                violation_error_message="A section must be associated with one group or district.",
                name="section_is_either_group_or_district",
            ),
            models.CheckConstraint(
                condition=models.Q(usual_weekday__isnull=False) | models.Q(section_type__in=NON_REGULAR_SECTIONS_TYPES),
                violation_error_message="A section must have a usual weekday, unless it is network or young leaders",
                name="regular_sections_must_have_usual_weekday",
            ),
            models.CheckConstraint(
                condition=(~models.Q(section_type=SectionType.EXPLORERS) | ~models.Q(nickname="")),
                violation_error_message="Explorer sections must have a nickname",
                name="explorers_must_have_nickname",
            ),
            models.UniqueConstraint(
                fields=["group", "section_type", "usual_weekday"],
                condition=models.Q(section_type__in=GROUP_SECTION_TYPES),
                violation_error_message="Only one group section of each type can be on a given weekday",
                name="ensure_only_one_section_type_per_weekday_per_group",
            ),
        ]

    @property
    def display_name(self) -> str:
        if self.group is not None:
            assert self.usual_weekday is not None  # enforced by check constraint
            identifier = self.nickname if self.nickname else self.usual_weekday.title()
            return f"{self.group.ordinal} {self.section_type.title()} ({identifier})"

        assert self.section_type in DISTRICT_SECTION_TYPES

        # Explorers always have a nickname
        # Young Leaders and Network use the nickname, or the district name.
        if self.section_type == SectionType.EXPLORERS or self.nickname:
            prefix = self.nickname.title()
        else:
            assert self.district is not None
            prefix = self.district.display_name

        section_type_display = SectionType(self.section_type).label
        return f"{prefix} {section_type_display}"

    def __str__(self) -> str:
        return self.display_name
