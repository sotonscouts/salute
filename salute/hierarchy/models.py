from django.db import models
from django_choices_field import TextChoicesField

from salute.core.models import Taxonomy
from salute.hierarchy.utils import get_ordinal_suffix
from salute.integrations.tsa.models import TSATimestampedObject

from .constants import (
    DISTRICT_SECTION_TYPES,
    GROUP_SECTION_TYPES,
    NON_REGULAR_SECTIONS_TYPES,
    SECTION_TYPE_INFO,
    GroupType,
    SectionOperatingCategory,
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


class Locality(Taxonomy):
    """
    A locality is a geographical area within a district.

    Sometimes a locality may encompass an entire district, but this is not always the case.
    A locality may also cross district boundaries.
    """

    class Meta:
        ordering = ("name",)
        constraints = [
            models.UniqueConstraint(
                fields=["name"],
                name="unique_locality_name",
                violation_error_message="A locality must have a unique name.",
            )
        ]
        verbose_name_plural = "localities"


class Group(TSAUnit):
    # TSA Fields
    district = models.ForeignKey(District, on_delete=models.PROTECT, related_name="groups")
    group_type = TextChoicesField(choices_enum=GroupType, editable=False)
    charity_number = models.PositiveIntegerField(null=True, editable=False)

    # Salute Fields
    locality = models.ForeignKey(Locality, on_delete=models.PROTECT, related_name="groups")
    local_unit_number = models.PositiveSmallIntegerField()
    location_name = models.CharField(max_length=255)
    primary_site = models.ForeignKey("locations.Site", on_delete=models.PROTECT, related_name="groups", null=True)

    @property
    def ordinal(self) -> str:
        suffix = get_ordinal_suffix(self.local_unit_number)
        return f"{self.local_unit_number}{suffix}"

    @property
    def display_name(self) -> str:
        return f"{self.ordinal} ({self.location_name})"

    @property
    def public_name(self) -> str:
        return f"{self.ordinal} {self.locality.name} ({self.location_name})"

    TSA_FIELDS = TSAUnit.TSA_FIELDS + ("district", "group_type", "charity_number")

    def __str__(self) -> str:
        return self.display_name

    class Meta:
        ordering = ("locality", "local_unit_number")

        constraints = [
            models.UniqueConstraint(
                fields=["local_unit_number", "locality"],
                name="unique_local_unit_number_within_locality",
                violation_error_message="A group must have a unique local unit number within its locality.",
            )
        ]


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
    mailing_slug = models.CharField(
        max_length=64,
        blank=True,
        help_text="Slug for generating mailing lists. Do not change unless you understand the impact. Only applicable to district sections.",  # noqa: E501
    )
    usual_weekday = TextChoicesField(choices_enum=Weekday, null=True)
    site = models.ForeignKey("locations.Site", on_delete=models.PROTECT, related_name="sections", null=True, blank=True)

    TSA_FIELDS = TSAUnit.TSA_FIELDS + ("district", "group", "section_type")

    class Meta:
        ordering = ("id",)
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
            models.CheckConstraint(
                condition=(models.Q(section_type__in=DISTRICT_SECTION_TYPES) | models.Q(mailing_slug="")),
                violation_error_message="Only district sections can have a mailing slug",
                name="only_district_sections_can_have_mailing_slug",
            ),
            # models.CheckConstraint(
            #     condition=(
            #         models.Q(section_type__in=GROUP_SECTION_TYPES, site__isnull=True)
            #         | models.Q(section_type__in=DISTRICT_SECTION_TYPES, site__isnull=False)
            #     ),
            #     violation_error_message="Only district sections must have a site",
            #     name="only_district_sections_must_have_site",
            # ),
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

        section_type_info = SECTION_TYPE_INFO[SectionType(self.section_type)]
        assert section_type_info["operating_category"] == SectionOperatingCategory.DISTRICT

        # Explorers always have a nickname
        # Young Leaders and Network use the nickname, or the district name.
        if self.section_type == SectionType.EXPLORERS or self.nickname:
            prefix = self.nickname.title()
        else:
            assert self.district is not None
            prefix = self.district.display_name

        section_type_display = section_type_info["display_name"]
        return f"{prefix} {section_type_display}"

    def __str__(self) -> str:
        return self.display_name
