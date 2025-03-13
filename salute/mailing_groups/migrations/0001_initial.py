import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("people", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="SystemMailingGroup",
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
                ("name", models.CharField(max_length=255, unique=True)),
                ("display_name", models.CharField(max_length=255)),
                ("composite_key", models.CharField(max_length=255, unique=True)),
                ("config", models.JSONField()),
                (
                    "can_receive_external_email",
                    models.BooleanField(
                        default=True,
                        help_text="Whether the group can receive emails externally.",
                    ),
                ),
                (
                    "can_members_send_as",
                    models.BooleanField(
                        default=False,
                        help_text="Whether members can send emails as the group address.",
                    ),
                ),
            ],
            options={
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="SystemMailingGroupMembership",
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
                    "person",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="people.person"),
                ),
                (
                    "system_mailing_group",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="mailing_groups.systemmailinggroup",
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="systemmailinggroup",
            name="members",
            field=models.ManyToManyField(
                related_name="system_mailing_groups",
                through="mailing_groups.SystemMailingGroupMembership",
                to="people.person",
            ),
        ),
        migrations.AddConstraint(
            model_name="systemmailinggroupmembership",
            constraint=models.UniqueConstraint(
                fields=("person", "system_mailing_group"),
                name="unique_person_system_mailing_group",
            ),
        ),
    ]
