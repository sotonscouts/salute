import uuid

import django.db.models.functions.comparison
import django.db.models.functions.text
import phonenumber_field.modelfields
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Person",
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
                ("legal_name", models.CharField(editable=False, max_length=255)),
                (
                    "preferred_name",
                    models.CharField(editable=False, max_length=255, null=True),
                ),
                ("last_name", models.CharField(editable=False, max_length=255)),
                (
                    "membership_number",
                    models.PositiveIntegerField(editable=False, unique=True, verbose_name="Membership Number"),
                ),
                ("is_suspended", models.BooleanField(editable=False)),
                (
                    "primary_email",
                    models.EmailField(editable=False, max_length=254, null=True),
                ),
                (
                    "default_email",
                    models.EmailField(editable=False, max_length=254, null=True),
                ),
                (
                    "alternate_email",
                    models.EmailField(editable=False, max_length=254, null=True),
                ),
                (
                    "phone_number",
                    phonenumber_field.modelfields.PhoneNumberField(blank=True, max_length=128, region=None),
                ),
                (
                    "first_name",
                    models.GeneratedField(
                        db_persist=True,
                        expression=django.db.models.functions.comparison.Coalesce(
                            models.F("preferred_name"), models.F("legal_name")
                        ),
                        output_field=models.CharField(max_length=511),
                    ),
                ),
                (
                    "display_name",
                    models.GeneratedField(
                        db_persist=True,
                        expression=django.db.models.functions.text.Concat(
                            models.F("first_name"),
                            models.Value(" "),
                            models.F("last_name"),
                        ),
                        output_field=models.CharField(max_length=511),
                    ),
                ),
                (
                    "tsa_email",
                    models.GeneratedField(
                        db_persist=True,
                        expression=django.db.models.functions.comparison.Coalesce(
                            models.F("primary_email"),
                            models.F("default_email"),
                            models.F("alternate_email"),
                        ),
                        output_field=models.EmailField(max_length=254),
                    ),
                ),
            ],
            options={
                "verbose_name": "Person",
                "verbose_name_plural": "People",
            },
        ),
    ]
