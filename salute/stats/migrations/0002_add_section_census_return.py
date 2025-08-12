import uuid

import django.db.models.deletion
import django.db.models.fields.json
import django.db.models.functions.comparison
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("hierarchy", "0004_add_primary_site_to_groups_and_sections"),
        ("stats", "0001_add_json_sum_functions"),
    ]

    operations = [
        migrations.CreateModel(
            name="SectionCensusReturn",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                        unique=True,
                        verbose_name="Salute ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "data_format_version",
                    models.PositiveSmallIntegerField(choices=[(1, "V1")], default=1),
                ),
                ("year", models.PositiveIntegerField()),
                ("data", models.JSONField()),
                (
                    "annual_subs_cost",
                    models.GeneratedField(
                        db_persist=True,
                        expression=django.db.models.functions.comparison.Cast(
                            django.db.models.fields.json.KeyTextTransform("annual_cost", "data"),
                            models.DecimalField(decimal_places=2, max_digits=6),
                        ),
                        output_field=models.DecimalField(decimal_places=2, max_digits=6),
                    ),
                ),
                (
                    "total_volunteers",
                    models.GeneratedField(
                        db_persist=True,
                        expression=models.Func(
                            models.F("data"),
                            models.Value("^l_[a-z]+_(m|f|p|s|xm|xf|xp|xs)$"),
                            function="j_sum_by_regex_key",
                        ),
                        output_field=models.IntegerField(),
                    ),
                ),
                (
                    "total_young_people",
                    models.GeneratedField(
                        db_persist=True,
                        expression=models.Func(
                            models.F("data"),
                            models.Value("^y_[0-9]+_(m|f|p|s)$"),
                            function="j_sum_by_regex_key",
                        ),
                        output_field=models.IntegerField(),
                    ),
                ),
                (
                    "ratio_young_people_to_volunteers",
                    models.GeneratedField(
                        db_persist=True,
                        expression=models.Func(
                            models.Func(
                                models.F("data"),
                                models.Value("^y_[0-9]+_(m|f|p|s)$"),
                                function="j_sum_by_regex_key",
                            ),
                            models.Func(
                                models.F("data"),
                                models.Value("^l_[a-z]+_(m|f|p|s|xm|xf|xp|xs)$"),
                                function="j_sum_by_regex_key",
                            ),
                            function="ratio",
                        ),
                        output_field=models.DecimalField(decimal_places=2, max_digits=6),
                    ),
                ),
                (
                    "section",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="census_returns",
                        to="hierarchy.section",
                    ),
                ),
            ],
            options={
                "ordering": ["-year"],
                "indexes": [models.Index(fields=["year"], name="idx_sectioncensusreturn_year")],
                "constraints": [models.UniqueConstraint(fields=("section", "year"), name="unique_section_year")],
            },
        ),
    ]
