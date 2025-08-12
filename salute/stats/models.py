from django.db import models
from django.db.models.fields.json import KeyTextTransform
from django.db.models.functions import Cast

from salute.core.models import BaseModel


class SectionCensusDataFormatVersion(models.IntegerChoices):
    """
    The format of the census data.
    """

    V1 = 1


TOTAL_VOLUNTEERS_EXPR = models.Func(
    models.F("data"),
    models.Value("^l_[a-z]+_(m|f|p|s|xm|xf|xp|xs)$"),
    function="j_sum_by_regex_key",
)

TOTAL_YOUNG_PEOPLE_EXPR = models.Func(
    models.F("data"),
    models.Value("^y_[0-9]+_(m|f|p|s)$"),
    function="j_sum_by_regex_key",
)


class SectionCensusReturn(BaseModel):
    section = models.ForeignKey(
        "hierarchy.Section",
        on_delete=models.PROTECT,
        related_name="census_returns",
    )
    data_format_version = models.PositiveSmallIntegerField(
        choices=SectionCensusDataFormatVersion.choices,
        default=SectionCensusDataFormatVersion.V1,
    )
    year = models.PositiveIntegerField()
    data = models.JSONField()

    annual_subs_cost = models.GeneratedField(
        expression=Cast(
            KeyTextTransform("annual_cost", "data"),
            models.DecimalField(max_digits=6, decimal_places=2),
        ),
        output_field=models.DecimalField(max_digits=6, decimal_places=2),
        db_persist=True,
    )

    total_volunteers = models.GeneratedField(
        expression=TOTAL_VOLUNTEERS_EXPR,
        output_field=models.IntegerField(),
        db_persist=True,
    )

    total_young_people = models.GeneratedField(
        expression=TOTAL_YOUNG_PEOPLE_EXPR,
        output_field=models.IntegerField(),
        db_persist=True,
    )

    ratio_young_people_to_volunteers = models.GeneratedField(
        expression=models.Func(
            TOTAL_YOUNG_PEOPLE_EXPR,
            TOTAL_VOLUNTEERS_EXPR,
            function="ratio",
        ),
        output_field=models.DecimalField(max_digits=6, decimal_places=2),
        db_persist=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["section", "year"],
                name="unique_section_year",
            ),
        ]
        ordering = ["-year"]
        indexes = [
            models.Index(fields=["year"], name="idx_sectioncensusreturn_year"),
        ]

    def __str__(self) -> str:
        return f"{self.section} - {self.year}"
