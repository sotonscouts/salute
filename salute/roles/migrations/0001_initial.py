import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("hierarchy", "0001_initial"),
        ("people", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="AccreditationType",
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
                ("name", models.CharField(max_length=255)),
            ],
            options={
                "ordering": ("name",),
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="RoleStatus",
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
                ("name", models.CharField(max_length=255)),
            ],
            options={
                "verbose_name_plural": "role statuses",
                "ordering": ("name",),
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="RoleType",
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
                ("name", models.CharField(max_length=255)),
            ],
            options={
                "ordering": ("name",),
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="TeamType",
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
                ("name", models.CharField(max_length=255)),
            ],
            options={
                "ordering": ("name",),
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="Team",
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
                ("allow_sub_team", models.BooleanField()),
                ("inherit_permissions", models.BooleanField()),
                (
                    "district",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="teams",
                        to="hierarchy.district",
                    ),
                ),
                (
                    "group",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="teams",
                        to="hierarchy.group",
                    ),
                ),
                (
                    "parent_team",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="sub_teams",
                        to="roles.team",
                    ),
                ),
                (
                    "section",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="teams",
                        to="hierarchy.section",
                    ),
                ),
                (
                    "team_type",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="roles.teamtype"),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Role",
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
                    "person",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="roles",
                        to="people.person",
                    ),
                ),
                (
                    "status",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="roles",
                        to="roles.rolestatus",
                    ),
                ),
                (
                    "role_type",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="roles",
                        to="roles.roletype",
                    ),
                ),
                (
                    "team",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="roles",
                        to="roles.team",
                    ),
                ),
            ],
            options={
                "ordering": ("team", "role_type", "person"),
            },
        ),
        migrations.CreateModel(
            name="Accreditation",
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
                ("status", models.CharField(max_length=64)),
                ("expires_at", models.DateTimeField()),
                ("granted_at", models.DateTimeField()),
                (
                    "person",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="accreditations",
                        to="people.person",
                    ),
                ),
                (
                    "accreditation_type",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="accreditations",
                        to="roles.accreditationtype",
                    ),
                ),
                (
                    "team",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="accreditations",
                        to="roles.team",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.AddConstraint(
            model_name="team",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    models.Q(
                        ("district__isnull", False),
                        ("group__isnull", True),
                        ("parent_team__isnull", True),
                        ("section__isnull", True),
                    ),
                    models.Q(
                        ("district__isnull", True),
                        ("group__isnull", False),
                        ("parent_team__isnull", True),
                        ("section__isnull", True),
                    ),
                    models.Q(
                        ("district__isnull", True),
                        ("group__isnull", True),
                        ("parent_team__isnull", True),
                        ("section__isnull", False),
                    ),
                    models.Q(
                        ("district__isnull", True),
                        ("group__isnull", True),
                        ("parent_team__isnull", False),
                        ("section__isnull", True),
                    ),
                    _connector="OR",
                ),
                name="team_only_has_one_parent_object",
                violation_error_message="A team must have exactly one parent",
            ),
        ),
        migrations.AddConstraint(
            model_name="team",
            constraint=models.UniqueConstraint(
                condition=models.Q(("district__isnull", False)),
                fields=("team_type", "district"),
                name="unique_team_within_district",
            ),
        ),
        migrations.AddConstraint(
            model_name="team",
            constraint=models.UniqueConstraint(
                condition=models.Q(("group__isnull", False)),
                fields=("team_type", "group"),
                name="unique_team_within_group",
            ),
        ),
        migrations.AddConstraint(
            model_name="team",
            constraint=models.UniqueConstraint(
                condition=models.Q(("section__isnull", False)),
                fields=("team_type", "section"),
                name="unique_team_within_section",
            ),
        ),
        migrations.AddConstraint(
            model_name="team",
            constraint=models.UniqueConstraint(
                condition=models.Q(("parent_team__isnull", False)),
                fields=("team_type", "parent_team"),
                name="unique_team_within_parent_team",
            ),
        ),
    ]
