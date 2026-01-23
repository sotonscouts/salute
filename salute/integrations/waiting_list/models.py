import datetime
from typing import Self

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Case, F, Value, When

from salute.core.models import BaseModel
from salute.hierarchy.constants import SECTION_TYPE_INFO, SectionType
from salute.hierarchy.models import Group, Section


class WaitingListUnit(BaseModel):
    name = models.CharField(max_length=255, unique=True)

    group = models.ForeignKey(Group, on_delete=models.PROTECT, related_name="waiting_list_units", null=True, blank=True)
    section = models.ForeignKey(
        Section, on_delete=models.PROTECT, related_name="waiting_list_units", null=True, blank=True
    )

    def clean(self) -> None:
        super().clean()
        if self.group is not None and self.section is not None:
            raise ValidationError("Group and section cannot both be set")

    def __str__(self) -> str:
        if self.group is not None:
            return self.group.display_name
        elif self.section is not None:
            return self.section.display_name
        else:
            return self.name

    class Meta:
        verbose_name = "Waiting List Unit"
        verbose_name_plural = "Waiting List Units"
        ordering = ["name"]


class TargetSection(models.TextChoices):
    TOO_YOUNG = "TOO_YOUNG", "Too Young"
    TOO_OLD = "TOO_OLD", "Too Old"


class WaitingListEntryQuerySet(models.QuerySet):
    def with_age(self, now: datetime.datetime) -> Self:
        """Annotate queryset with age as a duration/interval from date_of_birth."""
        today = now.date()
        return self.annotate(age=Value(today) - F("date_of_birth"))

    def with_target_section(self, now: datetime.datetime) -> Self:
        """Annotate queryset with target_section based on age."""
        today = now.date()
        age_interval = Value(today) - F("date_of_birth")

        # Extract days from the interval using DATE_PART
        age_days_expr = models.Func(
            Value("day"),
            age_interval,
            function="DATE_PART",
            template="%(function)s(%(expressions)s)",
            output_field=models.IntegerField(),
        )

        # First annotate age_days, then use it in Case/When
        queryset = self.annotate(_age_days=age_days_expr)

        # Build Case/When conditions for each section type using numeric ages
        when_conditions = []

        # Check sections in order (youngest to oldest)
        section_order = [
            SectionType.SQUIRRELS,
            SectionType.BEAVERS,
            SectionType.CUBS,
            SectionType.SCOUTS,
            SectionType.EXPLORERS,
            SectionType.NETWORK,
        ]

        for section_type in section_order:
            info = SECTION_TYPE_INFO[section_type]
            min_age = info["min_age_numeric"]
            max_age = info["max_age_numeric"]

            # Convert to days for comparison (approximate: 365.25 days per year)
            # max_age is inclusive, so we check < (max_age + 1) to include the full year
            min_days = int(min_age * 365.25)
            max_days_exclusive = int((max_age + 1) * 365.25)

            when_conditions.append(
                When(
                    _age_days__gte=min_days,
                    _age_days__lt=max_days_exclusive,
                    then=Value(section_type.name),
                )
            )

        # Add TOO_YOUNG (younger than youngest section)
        youngest_min = SECTION_TYPE_INFO[section_order[0]]["min_age_numeric"]
        when_conditions.insert(
            0,
            When(_age_days__lt=int(youngest_min * 365.25), then=Value(TargetSection.TOO_YOUNG.value)),
        )

        # Add TOO_OLD (older than oldest section)
        oldest_max = SECTION_TYPE_INFO[section_order[-1]]["max_age_numeric"]
        when_conditions.append(
            When(_age_days__gt=int(oldest_max * 365.25), then=Value(TargetSection.TOO_OLD.value)),
        )

        return queryset.annotate(target_section=Case(*when_conditions, default=Value(TargetSection.TOO_OLD.value)))


class WaitingListEntry(BaseModel):
    external_id = models.CharField(max_length=255, unique=True)
    joined_waiting_list_at = models.DateTimeField(db_index=True)

    units = models.ManyToManyField(WaitingListUnit, related_name="waiting_list_entries")
    date_of_birth = models.DateField(help_text="Rounded to the first of the month")
    postcode = models.CharField(max_length=255)

    successfully_transferred = models.BooleanField()

    objects = WaitingListEntryQuerySet.as_manager()

    class Meta:
        ordering = ["-joined_waiting_list_at"]
        indexes = [
            models.Index(fields=["date_of_birth"]),
            models.Index(fields=["postcode"]),
            models.Index(fields=["successfully_transferred"]),
        ]

    def __str__(self) -> str:
        return self.external_id


class WaitingListSectionRecord(BaseModel):
    section = models.ForeignKey(Section, on_delete=models.PROTECT)
    date = models.DateField()
    waiting_list_count = models.IntegerField()

    def __str__(self) -> str:
        return f"{self.section.display_name} - {self.date} - {self.waiting_list_count}"

    class Meta:
        ordering = ["-date"]
        constraints = [
            models.UniqueConstraint(fields=["section", "date"], name="unique_waiting_list_section_date"),
        ]


class WaitingListSectionType(models.TextChoices):
    TOO_YOUNG = "TOO_YOUNG", "Too Young"
    TOO_OLD = "TOO_OLD", "Too Old"
    SQUIRRELS = "SQUIRRELS", "Squirrels"
    BEAVERS = "BEAVERS", "Beavers"
    CUBS = "CUBS", "Cubs"
    SCOUTS = "SCOUTS", "Scouts"
    EXPLORERS = "EXPLORERS", "Explorers"
    NETWORK = "NETWORK", "Network"


class WaitingListSectionTypeRecord(BaseModel):
    section_type = models.CharField(max_length=30, choices=WaitingListSectionType.choices)
    date = models.DateField()
    waiting_list_count = models.IntegerField()

    def __str__(self) -> str:
        return f"{self.section_type} - {self.date} - {self.waiting_list_count}"

    class Meta:
        ordering = ["-date"]
        constraints = [
            models.UniqueConstraint(fields=["section_type", "date"], name="unique_waiting_list_section_type_date"),
        ]
