import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("hierarchy", "0006_add_osm_id_field"),
    ]

    operations = [
        migrations.CreateModel(
            name="OSMSyncLog",
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
                ("date", models.DateField()),
                ("data", models.JSONField()),
                ("error", models.TextField(blank=True)),
                ("success", models.BooleanField()),
            ],
            options={
                "ordering": ("-date",),
            },
        ),
        migrations.CreateModel(
            name="OSMSectionHeadcountRecord",
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
                ("date", models.DateField()),
                ("young_person_count", models.IntegerField()),
                ("adult_count", models.IntegerField()),
                (
                    "section",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="osm_section_headcount_records",
                        to="hierarchy.section",
                    ),
                ),
                (
                    "sync_log",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="osm_section_headcount_records",
                        to="osm.osmsynclog",
                    ),
                ),
            ],
            options={
                "ordering": ("date",),
                "constraints": [models.UniqueConstraint(fields=("section", "date"), name="unique_section_date")],
            },
        ),
    ]
