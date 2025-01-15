import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="District",
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
                    "tsa_id",
                    models.UUIDField(editable=False, unique=True, verbose_name="TSA ID"),
                ),
                (
                    "tsa_last_modified",
                    models.DateTimeField(editable=False, verbose_name="TSA Last Modified at"),
                ),
                ("unit_name", models.CharField(editable=False, max_length=255)),
                ("shortcode", models.CharField(editable=False, max_length=9)),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="Group",
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
                    "tsa_id",
                    models.UUIDField(editable=False, unique=True, verbose_name="TSA ID"),
                ),
                (
                    "tsa_last_modified",
                    models.DateTimeField(editable=False, verbose_name="TSA Last Modified at"),
                ),
                ("unit_name", models.CharField(editable=False, max_length=255)),
                ("shortcode", models.CharField(editable=False, max_length=9)),
                (
                    "group_type",
                    models.CharField(
                        choices=[("Air", "Air"), ("Land", "Land"), ("Sea", "Sea")],
                        editable=False,
                        max_length=10,
                    ),
                ),
                (
                    "charity_number",
                    models.PositiveIntegerField(editable=False, null=True),
                ),
                (
                    "local_unit_number",
                    models.PositiveSmallIntegerField(null=True, unique=True),
                ),
                ("location_name", models.CharField(max_length=255, null=True)),
                (
                    "district",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="groups",
                        to="hierarchy.district",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="Section",
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
                    "tsa_id",
                    models.UUIDField(editable=False, unique=True, verbose_name="TSA ID"),
                ),
                (
                    "tsa_last_modified",
                    models.DateTimeField(editable=False, verbose_name="TSA Last Modified at"),
                ),
                ("unit_name", models.CharField(editable=False, max_length=255)),
                ("shortcode", models.CharField(editable=False, max_length=9)),
                (
                    "section_type",
                    models.CharField(
                        choices=[
                            ("Squirrels", "Squirrels"),
                            ("Beavers", "Beavers"),
                            ("Cubs", "Cubs"),
                            ("Scouts", "Scouts"),
                            ("Explorers", "Explorers"),
                            ("Network", "Network"),
                        ],
                        editable=False,
                        max_length=10,
                    ),
                ),
                (
                    "district",
                    models.ForeignKey(
                        editable=False,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="sections",
                        to="hierarchy.district",
                    ),
                ),
                (
                    "group",
                    models.ForeignKey(
                        editable=False,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="sections",
                        to="hierarchy.group",
                    ),
                ),
            ],
            options={
                "constraints": [
                    models.CheckConstraint(
                        condition=models.Q(
                            models.Q(
                                ("district__isnull", False),
                                ("group__isnull", True),
                                ("section_type__in", ["Explorers", "Network"]),
                            ),
                            models.Q(
                                ("district__isnull", True),
                                ("group__isnull", False),
                                (
                                    "section_type__in",
                                    ["Squirrels", "Beavers", "Cubs", "Scouts"],
                                ),
                            ),
                            _connector="OR",
                        ),
                        name="section_is_either_group_or_district",
                        violation_error_message="A section must be associated with one group or district.",
                    )
                ],
            },
        ),
    ]
