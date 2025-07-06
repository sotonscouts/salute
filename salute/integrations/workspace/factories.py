import zoneinfo
from typing import Any

import factory

from salute.integrations.workspace.models import WorkspaceAccount, WorkspaceGroup


class WorkspaceAccountFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = WorkspaceAccount

    google_id = factory.Faker("first_name")
    primary_email = factory.Faker("email")
    given_name = factory.Faker("first_name")
    family_name = factory.Faker("last_name")

    # Editable Flags
    archived = False
    change_password_at_next_login = False
    suspended = False

    agreed_to_terms = False
    external_ids: dict[str, Any] = {}
    is_admin = False
    is_delegated_admin = False
    is_enforced_in_2sv = True
    is_enrolled_in_2sv = True
    org_unit_path = "/People"

    # Security
    has_recovery_email = True
    has_recovery_phone = True

    # Timestamps
    creation_time = factory.Faker("past_datetime", tzinfo=zoneinfo.ZoneInfo("Europe/London"))
    last_login_time = factory.Faker("past_datetime", tzinfo=zoneinfo.ZoneInfo("Europe/London"))


class WorkspaceGroupFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = WorkspaceGroup

    google_id = factory.Faker("uuid4")
    email = factory.Faker("email")
    name = factory.Faker("company")
    description = factory.Faker("sentence")
