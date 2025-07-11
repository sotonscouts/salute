# Generated by Django 5.1.5 on 2025-02-01 09:28

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
            name="WorkspaceGroup",
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
                    "google_id",
                    models.CharField(editable=False, max_length=100, unique=True),
                ),
                (
                    "email",
                    models.CharField(editable=False, max_length=255, unique=True),
                ),
                ("name", models.CharField(editable=False, max_length=255)),
                ("description", models.TextField(editable=False)),
                ("salute_managed", models.BooleanField(default=False, editable=False)),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="WorkspaceAccount",
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
                    "google_id",
                    models.CharField(editable=False, max_length=100, unique=True),
                ),
                (
                    "primary_email",
                    models.CharField(editable=False, max_length=255, unique=True),
                ),
                ("given_name", models.CharField(editable=False, max_length=255)),
                ("family_name", models.CharField(editable=False, max_length=255)),
                ("archived", models.BooleanField(editable=False)),
                ("change_password_at_next_login", models.BooleanField(editable=False)),
                ("suspended", models.BooleanField(editable=False)),
                ("agreed_to_terms", models.BooleanField(editable=False)),
                ("external_ids", models.JSONField(editable=False)),
                ("is_admin", models.BooleanField(editable=False)),
                ("is_delegated_admin", models.BooleanField(editable=False)),
                ("is_enforced_in_2sv", models.BooleanField(editable=False)),
                ("is_enrolled_in_2sv", models.BooleanField(editable=False)),
                ("org_unit_path", models.CharField(editable=False, max_length=255)),
                ("has_recovery_email", models.BooleanField(editable=False)),
                ("has_recovery_phone", models.BooleanField(editable=False)),
                ("creation_time", models.DateTimeField(editable=False)),
                ("last_login_time", models.DateTimeField(editable=False, null=True)),
                (
                    "person",
                    models.OneToOneField(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="workspace_account",
                        to="people.person",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="WorkspaceAccountAlias",
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
                    "address",
                    models.EmailField(editable=False, max_length=254, unique=True),
                ),
                (
                    "account",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="aliases",
                        to="workspace.workspaceaccount",
                    ),
                ),
            ],
            options={
                "verbose_name": "Workspace Account Alias",
                "verbose_name_plural": "Workspace Account Aliases",
            },
        ),
        migrations.CreateModel(
            name="WorkspaceGroupAlias",
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
                    "address",
                    models.EmailField(editable=False, max_length=254, unique=True),
                ),
                (
                    "group",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="aliases",
                        to="workspace.workspacegroup",
                    ),
                ),
            ],
            options={
                "verbose_name": "Workspace Group Alias",
                "verbose_name_plural": "Workspace Group Aliases",
            },
        ),
    ]
